"""Function-scoped AST scanner for unsafe process-termination patterns."""

import ast
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


def _dotted(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _dotted(node.value)
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


def _owned_values(scope):
    processes = set()
    pids = set()
    for node in _scope_nodes(scope):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        names = {name for target in targets for name in _assigned_names(target)}
        value = node.value
        if isinstance(value, ast.Call) and _dotted(value.func) == "subprocess.Popen":
            processes.update(names)
        if isinstance(value, ast.Call) and _dotted(value.func) == "os.fork":
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


def _is_owned_process(node, processes, pids):
    if isinstance(node, ast.Name):
        return node.id in processes
    if isinstance(node, ast.Call) and _dotted(node.func) == "subprocess.Popen":
        return True
    return (
        isinstance(node, ast.Call)
        and _dotted(node.func) == "psutil.Process"
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


def _shell_kill_target(call):
    if _dotted(call.func) not in SHELL_LAUNCHERS or not call.args:
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


def _unsafe_termination(call, processes, pids):
    name = _dotted(call.func)
    if name in {"os.kill", "os.killpg", "signal.pthread_kill"}:
        return not call.args or not _is_owned_pid(call.args[0], processes, pids)
    if isinstance(call.func, ast.Attribute) and call.func.attr in TERMINATION_METHODS:
        return not _is_owned_process(call.func.value, processes, pids)
    target = _shell_kill_target(call)
    if target is None:
        return False
    if isinstance(target, ast.AST):
        if (
            isinstance(target, ast.Call)
            and _dotted(target.func) == "str"
            and target.args
        ):
            target = target.args[0]
        return not _is_owned_pid(target, processes, pids)
    return True


def scan_python_path(path, *, display_path=None):
    """Return unsafe termination sites grouped by function or module scope."""
    path = Path(path)
    label = Path(display_path) if display_path is not None else path
    tree = ast.parse(path.read_text(), filename=str(path))
    scopes = [("<module>", tree)]
    scopes.extend(
        (node.name, node)
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    )
    dangerous = set()
    lines = {}
    for name, scope in scopes:
        processes, pids = _owned_values(scope)
        for node in _scope_nodes(scope):
            if isinstance(node, ast.Call) and _unsafe_termination(
                node, processes, pids
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
                if isinstance(node, ast.Call) and _dotted(node.func) in dangerous:
                    dangerous.add(name)
                    lines[name] = node.lineno
                    changed = True
                    break
    return [f"{label}:{lines[name]}:{name}" for name, _ in scopes if name in dangerous]
