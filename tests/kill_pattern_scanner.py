"""Function-scoped AST scanner for unsafe process-termination patterns."""

import ast
import re
import shlex
from pathlib import Path

TERMINATION_METHODS = {"kill", "send_signal", "terminate"}
SHELL_LAUNCHERS = {
    "os.system",
    "subprocess.call",
    "subprocess.check_call",
    "subprocess.check_output",
    "subprocess.Popen",
    "subprocess.run",
}

SHELL_WRAPPERS = {
    "builtin",
    "command",
    "exec",
    "env",
    "nice",
    "sudo",
    "timeout",
    "xargs",
}


def _import_bindings(tree):
    """Map imported names to their canonical dotted names for one module."""
    bindings = {}
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                bindings[alias.asname or alias.name.split(".")[0]] = alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                bindings[alias.asname or alias.name] = f"{node.module}.{alias.name}"
    return bindings


def _dotted(node, bindings=None):
    if isinstance(node, ast.Name):
        return (bindings or {}).get(node.id, node.id)
    if isinstance(node, ast.Attribute):
        prefix = _dotted(node.value, bindings)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def _scope_nodes(scope):
    """Yield nodes in one module/function without descending into child scopes."""
    stack = list(ast.iter_child_nodes(scope))
    while stack:
        node = stack.pop()
        if isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)
        ):
            continue
        yield node
        stack.extend(ast.iter_child_nodes(node))


def _assigned_names(target):
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, (ast.Tuple, ast.List)):
        return {name for item in target.elts for name in _assigned_names(item)}
    return set()


def _owned_values(scope, bindings):
    processes = set()
    pids = set()
    for node in _scope_nodes(scope):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        names = {name for target in targets for name in _assigned_names(target)}
        value = node.value
        if (
            isinstance(value, ast.Call)
            and _dotted(value.func, bindings) == "subprocess.Popen"
        ):
            processes.update(names)
        if isinstance(value, ast.Call) and _dotted(value.func, bindings) == "os.fork":
            pids.update(names)
    return processes, pids


def _is_owned_pid(node, processes, pids):
    if isinstance(node, ast.Name):
        return node.id in pids
    return (
        isinstance(node, ast.Attribute)
        and node.attr == "pid"
        and isinstance(node.value, ast.Name)
        and node.value.id in processes
    )


def _is_owned_process(node, processes, pids, bindings):
    if isinstance(node, ast.Name):
        return node.id in processes
    if (
        isinstance(node, ast.Call)
        and _dotted(node.func, bindings) == "subprocess.Popen"
    ):
        return True
    return (
        isinstance(node, ast.Call)
        and _dotted(node.func, bindings) == "psutil.Process"
        and bool(node.args)
        and _is_owned_pid(node.args[0], processes, pids)
    )


def _literal_shell_tokens(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        try:
            return shlex.split(node.value)
        except ValueError:
            return []
    if isinstance(node, (ast.List, ast.Tuple)):
        tokens = []
        for item in node.elts:
            if isinstance(item, ast.Constant) and isinstance(item.value, (str, int)):
                tokens.append(str(item.value))
            else:
                tokens.append(item)
        return tokens
    return []


def _shell_kill_target(call, bindings):
    if _dotted(call.func, bindings) not in SHELL_LAUNCHERS or not call.args:
        return None
    tokens = _literal_shell_tokens(call.args[0])
    for index, token in enumerate(tokens):
        if isinstance(token, str) and Path(token).name in {"pkill", "killall"}:
            return token
        if isinstance(token, str) and Path(token).name == "kill":
            remaining = tokens[index + 1 :]
            i = 0
            while i < len(remaining):
                token = remaining[i]
                if token in {"-s", "--signal"}:
                    i += 2
                    continue
                if isinstance(token, str) and token.startswith("-"):
                    i += 1
                    continue
                return token
            return "missing-target"
    return None


def _unsafe_termination(call, processes, pids, bindings):
    name = _dotted(call.func, bindings)
    if name in {"os.kill", "os.killpg", "signal.pthread_kill"}:
        return not call.args or not _is_owned_pid(call.args[0], processes, pids)
    if isinstance(call.func, ast.Attribute) and call.func.attr in TERMINATION_METHODS:
        return not _is_owned_process(call.func.value, processes, pids, bindings)
    target = _shell_kill_target(call, bindings)
    if target is None:
        return False
    if isinstance(target, ast.AST):
        if (
            isinstance(target, ast.Call)
            and _dotted(target.func, bindings) == "str"
            and target.args
        ):
            target = target.args[0]
        return not _is_owned_pid(target, processes, pids)
    return True


def _shell_tokens(line):
    try:
        lexer = shlex.shlex(line, posix=True, punctuation_chars=";&|")
        lexer.whitespace_split = True
        lexer.commenters = "#"
        return list(lexer)
    except ValueError:
        return []


def _shell_command_groups(tokens):
    group = []
    for token in tokens:
        if token and set(token) <= {";", "&", "|"}:
            if group:
                yield group
                group = []
        else:
            group.append(token)
    if group:
        yield group


def _shell_command_index(tokens):
    index = 0
    while index < len(tokens):
        token = Path(tokens[index]).name
        if "=" in tokens[index] and not tokens[index].startswith("="):
            index += 1
            continue
        if token not in SHELL_WRAPPERS:
            break
        index += 1
        while index < len(tokens) and tokens[index].startswith("-"):
            option = tokens[index]
            index += 1
            if option in {"-u", "-g", "-n", "-I", "--user", "--group"}:
                index += 1
        if token == "timeout" and index < len(tokens):
            index += 1
        while token == "env" and index < len(tokens) and "=" in tokens[index]:
            index += 1
    return index


def _shell_owned_target(token, owned_names):
    if token in {"$!", "${!}", "$$", "${$}"}:
        return True
    match = re.fullmatch(r"\$\{?([A-Za-z_]\w*)\}?", token)
    return bool(match and match.group(1) in owned_names)


def _unsafe_shell_group(tokens, owned_names):
    index = _shell_command_index(tokens)
    if index >= len(tokens):
        return False
    process = Path(tokens[index]).name
    if process in {"pkill", "killall"}:
        return True
    if process != "kill":
        return False
    targets = []
    index += 1
    while index < len(tokens):
        token = tokens[index]
        if token in {"-n", "-s", "--signal"}:
            index += 2
            continue
        if token.startswith("-"):
            index += 1
            continue
        targets.append(token)
        index += 1
    return not targets or any(
        not _shell_owned_target(target, owned_names) for target in targets
    )


def _scan_shell_text(text, label, *, line_offset=0):
    hits = []
    scope = "<shell>"
    depth = 0
    owned_by_scope = {scope: set()}
    function_pattern = re.compile(
        r"^\s*(?:function\s+)?([A-Za-z_]\w*)\s*(?:\(\s*\))?\s*\{"
    )
    for line_number, line in enumerate(text.splitlines(), start=1 + line_offset):
        function = function_pattern.match(line)
        if function and depth == 0:
            scope = function.group(1)
            owned_by_scope.setdefault(scope, set())
        for name, value in re.findall(r"\b([A-Za-z_]\w*)=(\$!|\$\$)", line):
            if value in {"$!", "$$"}:
                owned_by_scope[scope].add(name)
        tokens = _shell_tokens(line)
        if function and tokens:
            tokens = tokens[1:]
        for group in _shell_command_groups(tokens):
            if _unsafe_shell_group(group, owned_by_scope[scope]):
                hits.append(f"{label}:{line_number}:{scope}")
                break
        depth += line.count("{") - line.count("}")
        if depth <= 0:
            depth = 0
            scope = "<shell>"
    return hits


def scan_shell_path(path, *, display_path=None):
    """Return unsafe shell termination sites grouped by function or file scope."""
    path = Path(path)
    label = Path(display_path) if display_path is not None else path
    return _scan_shell_text(path.read_text(), label)


def scan_python_path(path, *, display_path=None):
    """Return unsafe termination sites grouped by function or module scope."""
    path = Path(path)
    label = Path(display_path) if display_path is not None else path
    tree = ast.parse(path.read_text(), filename=str(path))
    bindings = _import_bindings(tree)
    scopes = [("<module>", tree)]
    scopes.extend(
        (node.name, node)
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    )
    dangerous = set()
    lines = {}
    for name, scope in scopes:
        processes, pids = _owned_values(scope, bindings)
        for node in _scope_nodes(scope):
            if isinstance(node, ast.Call) and _unsafe_termination(
                node, processes, pids, bindings
            ):
                dangerous.add(name)
                lines.setdefault(name, node.lineno)

    # A watcher that delegates to a dangerous helper remains visible across lines.
    changed = True
    while changed:
        changed = False
        for name, scope in scopes:
            if name in dangerous:
                continue
            for node in _scope_nodes(scope):
                if (
                    isinstance(node, ast.Call)
                    and _dotted(node.func, bindings) in dangerous
                ):
                    dangerous.add(name)
                    lines[name] = node.lineno
                    changed = True
                    break
    hits = [f"{label}:{lines[name]}:{name}" for name, _ in scopes if name in dangerous]
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and "\n" in node.value
        ):
            hits.extend(
                _scan_shell_text(node.value, label, line_offset=node.lineno - 1)
            )
    return list(dict.fromkeys(hits))
