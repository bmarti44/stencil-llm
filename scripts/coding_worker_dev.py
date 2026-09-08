#!/usr/bin/env python3
"""CPU-only validator and executable preflight for coding self-cue DEV data.

This module does not contact a model or launch a server.  It validates one
Kimi-authored episode (or a four-episode bank), applies references and mutants
through the future worker consumer, and runs every check in a fresh existing
SLAB seccomp worker.
"""

import argparse
import ast
import hashlib
import json
import math
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from stencil.focus import slab
from stencil.focus.renderer import compact

SCHEMA_VERSION = 1
EXPECTED_EPISODES = 4
EXPECTED_ROUNDS = 6
GENERATION_CAP = 768
MIN_GENERATION_HEADROOM = 128
MAX_MODULE_BYTES = 65_536
MAX_RESPONSE_BYTES = 65_536

TOP_KEYS = {"schema_version", "split", "author", "lineage", "episode"}
AUTHOR_KEYS = {"name", "model"}
LINEAGE_KEYS = {"fit_on", "development_on", "evaluated_on"}
EPISODE_KEYS = {
    "episode_id",
    "project",
    "task_handles",
    "initial_file",
    "initial_checks",
    "rounds",
}
INITIAL_FILE_KEYS = {"path", "text"}
ROUND_KEYS = {
    "index",
    "source_messages",
    "request",
    "target",
    "manual_recap",
    "oracle",
    "reference_patch",
    "functional_checks",
    "obligation_checks",
    "negative_controls",
}
MESSAGE_KEYS = {"message_id", "role", "text"}
REQUEST_KEYS = {"message_id", "role", "task_handle", "text"}
TARGET_KEYS = {"path", "symbol"}
ORACLE_KEYS = {"effective_rules", "inactive_rule_ids"}
RULE_KEYS = {"rule_id", "scope", "strength", "text", "source_ids"}
CHECK_KEYS = {
    "check_id",
    "symbol",
    "input",
    "expected_values",
    "rule_ids",
}
CONTROL_KEYS = {"control_id", "kind", "patch", "expected_failing_check_ids"}
RULE_STRENGTHS = {"required", "prohibited", "permitted", "optional"}
SOURCE_ROLES = {"user", "assistant"}
SAFE_PATH = re.compile(r"[A-Za-z][A-Za-z0-9_-]*\.py")
SAFE_SYMBOL = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
FORBIDDEN_CALLS = {
    "__import__",
    "breakpoint",
    "compile",
    "eval",
    "exec",
    "exit",
    "globals",
    "help",
    "input",
    "locals",
    "open",
    "print",
    "quit",
    "vars",
}


class ValidationError(ValueError):
    """Authored data violates the frozen schema or task contract."""


class PatchError(ValueError):
    """A worker-shaped response cannot be consumed exactly."""


@dataclass(frozen=True)
class ParsedPatch:
    prefix: str
    fence: str
    path: str
    symbol: str
    code: str


def sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def sha256_text(value):
    return sha256_bytes(value.encode("utf-8"))


def _require_object(value, label):
    if type(value) is not dict:
        raise ValidationError(f"{label} must be an object")
    return value


def _require_keys(value, expected, label):
    _require_object(value, label)
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ValidationError(f"{label} keys: missing={missing}, extra={extra}")


def _require_string(value, label, *, allow_empty=False):
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        raise ValidationError(f"{label} must be a nonempty string")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValidationError(f"{label} must contain Unicode scalars") from exc
    return value


def _require_string_list(value, label, *, nonempty=False, unique=True):
    if type(value) is not list or (nonempty and not value):
        qualifier = "nonempty " if nonempty else ""
        raise ValidationError(f"{label} must be a {qualifier}list")
    for index, item in enumerate(value):
        _require_string(item, f"{label}[{index}]")
    if unique and len(set(value)) != len(value):
        raise ValidationError(f"{label} must not contain duplicates")
    return value


def _require_sequence(value, label, *, length=None, minimum=None):
    if type(value) is not list:
        raise ValidationError(f"{label} must be a list")
    if length is not None and len(value) != length:
        raise ValidationError(f"{label} must contain exactly {length} items")
    if minimum is not None and len(value) < minimum:
        raise ValidationError(f"{label} must contain at least {minimum} items")
    return value


def _require_json(value, label):
    if value is None or type(value) in {bool, int, str}:
        if isinstance(value, str):
            _require_string(value, label, allow_empty=True)
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise ValidationError(f"{label} must not contain NaN or infinity")
        return
    if type(value) is list:
        for index, item in enumerate(value):
            _require_json(item, f"{label}[{index}]")
        return
    if type(value) is dict:
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValidationError(f"{label} object keys must be strings")
            _require_string(key, f"{label} key", allow_empty=True)
            _require_json(item, f"{label}[{key!r}]")
        return
    raise ValidationError(f"{label} is not a JSON value")


def json_equal(left, right):
    """JSON equality that keeps bool, int, and float distinct."""
    if type(left) is not type(right):
        return False
    if type(left) is list:
        return len(left) == len(right) and all(
            json_equal(a, b) for a, b in zip(left, right, strict=True)
        )
    if type(left) is dict:
        return left.keys() == right.keys() and all(
            json_equal(left[key], right[key]) for key in left
        )
    return left == right


def _safe_path(value, label):
    value = _require_string(value, label)
    if SAFE_PATH.fullmatch(value) is None or Path(value).name != value:
        raise ValidationError(f"{label} must be one safe module filename")
    return value


def _safe_symbol(value, label):
    value = _require_string(value, label)
    if SAFE_SYMBOL.fullmatch(value) is None or value.startswith("__"):
        raise ValidationError(f"{label} must be a safe Python symbol")
    return value


def _parse_python(code, label, error_type=ValidationError):
    try:
        return ast.parse(code)
    except (SyntaxError, RecursionError) as exc:
        raise error_type(f"{label} is not valid Python: {exc}") from exc


def _validate_function(node, symbol, label, error_type=ValidationError):
    if not isinstance(node, ast.FunctionDef) or node.name != symbol:
        raise error_type(f"{label} must define only {symbol}")
    if node.col_offset != 0:
        raise error_type(f"{label} function def must start at column zero")
    if node.decorator_list:
        raise error_type(f"{label} must not use decorators")
    args = node.args
    positional = len(args.posonlyargs) + len(args.args)
    if (
        positional != 1
        or args.vararg is not None
        or args.kwarg is not None
        or args.kwonlyargs
        or args.defaults
    ):
        raise error_type(f"{label} must take exactly one positional argument")
    for child in ast.walk(node):
        if child is not node and isinstance(
            child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        ):
            raise error_type(f"{label} must not define nested callables or classes")
        if isinstance(child, (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal)):
            raise error_type(f"{label} contains a prohibited statement")
        if isinstance(child, ast.Name) and child.id.startswith("__"):
            raise error_type(f"{label} contains a prohibited dunder name")
        if isinstance(child, ast.Attribute) and child.attr.startswith("__"):
            raise error_type(f"{label} contains a prohibited dunder attribute")
        if (
            isinstance(child, ast.Call)
            and isinstance(child.func, ast.Name)
            and child.func.id in FORBIDDEN_CALLS
        ):
            raise error_type(f"{label} calls prohibited builtin {child.func.id}")
    return node


def _parse_single_function(code, symbol, label, error_type=ValidationError):
    tree = _parse_python(code, label, error_type)
    if len(tree.body) != 1:
        raise error_type(f"{label} must contain exactly one top-level definition")
    node = _validate_function(tree.body[0], symbol, label, error_type)
    try:
        compile(code, f"<{label}>", "exec")
    except (SyntaxError, ValueError, OverflowError) as exc:
        raise error_type(f"{label} does not compile: {exc}") from exc
    return node


def parse_response(output, expected_path, expected_symbol):
    """Parse exactly one fenced function without changing submitted code bytes."""
    if not isinstance(output, str):
        raise PatchError("response must be a string")
    try:
        encoded = output.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise PatchError("response must contain Unicode scalars") from exc
    if len(encoded) > MAX_RESPONSE_BYTES:
        raise PatchError("response exceeds byte limit")
    if "\r" in output:
        raise PatchError("response must use LF line endings")
    if output.count("```") != 2 or "````" in output or "~~~" in output:
        raise PatchError("response must contain exactly one triple-backtick fence")
    match = re.search(
        r"```python (?P<path>[A-Za-z][A-Za-z0-9_-]*\.py)\n"
        r"(?P<code>[\s\S]*?)\n```",
        output,
    )
    if match is None:
        raise PatchError("response fence must be ```python <path> with code")
    if output[match.end() :].strip():
        raise PatchError("response must not contain trailing prose")
    path = match.group("path")
    if path != expected_path:
        raise PatchError(f"wrong target path: {path!r}")
    code = match.group("code")
    if not code.strip():
        raise PatchError("response code must be nonempty")
    node = _parse_single_function(
        code, expected_symbol, "response patch", PatchError
    )
    return ParsedPatch(
        prefix=output[: match.start()],
        fence=match.group(0),
        path=path,
        symbol=node.name,
        code=code,
    )


def fenced_response(path, patch, prefix=""):
    """Construct the exact worker-shaped response used by CPU gold controls."""
    _safe_path(path, "fence path")
    _require_string(patch, "patch")
    _require_string(prefix, "prefix", allow_empty=True)
    if "\r" in patch or "```" in patch:
        raise ValidationError("patch cannot contain CR or a code fence")
    lead = prefix + ("\n" if prefix and not prefix.endswith("\n") else "")
    close_gap = "" if patch.endswith("\n") else "\n"
    return f"{lead}```python {path}\n{patch}{close_gap}```"


def splice_function(module_text, patch, symbol):
    """Replace one top-level function using AST extents and exact patch content."""
    if not isinstance(module_text, str) or not isinstance(patch, str):
        raise PatchError("module and patch must be strings")
    tree = _parse_python(module_text, "current module", PatchError)
    matches = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == symbol
    ]
    if len(matches) != 1:
        raise PatchError(f"current module must contain one {symbol} definition")
    _parse_single_function(patch, symbol, "response patch", PatchError)
    node = matches[0]
    # AST line coordinates follow Python physical lines.  str.splitlines()
    # additionally splits U+0085, U+2028/U+2029 and several control separators,
    # which can shift the slice and leave stale code in the module.
    lines = re.findall(r"[^\r\n]*(?:\r\n|\r|\n|$)", module_text)
    if lines and lines[-1] == "":
        lines.pop()
    if "".join(lines) != module_text:
        raise PatchError("could not preserve physical source lines")
    before = "".join(lines[: node.lineno - 1])
    after = "".join(lines[node.end_lineno :])
    separator = "\n" if after and not patch.endswith(("\n", "\r")) else ""
    merged = before + patch + separator + after
    if len(merged.encode("utf-8")) > MAX_MODULE_BYTES:
        raise PatchError("spliced module exceeds byte limit")
    _parse_python(merged, "spliced module", PatchError)
    try:
        compile(merged, "<spliced module>", "exec")
    except (SyntaxError, ValueError, OverflowError) as exc:
        raise PatchError(f"spliced module does not compile: {exc}") from exc
    return merged


def consume_patch(module_text, path, symbol, patch, *, prefix=""):
    response = fenced_response(path, patch, prefix)
    parsed = parse_response(response, path, symbol)
    return parsed, splice_function(module_text, parsed.code, symbol)


def _is_none_stub(node):
    body = list(node.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(
        body[0].value, ast.Constant
    ) and isinstance(body[0].value.value, str):
        body.pop(0)
    return (
        len(body) == 1
        and isinstance(body[0], ast.Return)
        and isinstance(body[0].value, ast.Constant)
        and body[0].value.value is None
    )


def _validate_check(value, label, symbols, *, obligation=False):
    _require_keys(value, CHECK_KEYS, label)
    _require_string(value["check_id"], f"{label}.check_id")
    symbol = _safe_symbol(value["symbol"], f"{label}.symbol")
    if symbol not in symbols:
        raise ValidationError(f"{label}.symbol is absent from the module")
    _require_json(value["input"], f"{label}.input")
    expected = _require_sequence(
        value["expected_values"], f"{label}.expected_values", minimum=1
    )
    for index, item in enumerate(expected):
        _require_json(item, f"{label}.expected_values[{index}]")
    if any(
        json_equal(expected[left], expected[right])
        for left in range(len(expected))
        for right in range(left + 1, len(expected))
    ):
        raise ValidationError(f"{label}.expected_values contains duplicates")
    rule_ids = _require_string_list(value["rule_ids"], f"{label}.rule_ids")
    if obligation and not rule_ids:
        raise ValidationError(f"{label}.rule_ids must identify current rules")
    if not obligation and rule_ids:
        raise ValidationError(f"{label}.rule_ids must be empty for functionality")


def _validate_rule(value, label, task_handles, source_roles):
    _require_keys(value, RULE_KEYS, label)
    _require_string(value["rule_id"], f"{label}.rule_id")
    scope = value["scope"]
    if scope is not None and scope not in task_handles:
        raise ValidationError(f"{label}.scope must be null or a task handle")
    if value["strength"] not in RULE_STRENGTHS:
        raise ValidationError(f"{label}.strength is invalid")
    _require_string(value["text"], f"{label}.text")
    source_ids = _require_string_list(
        value["source_ids"], f"{label}.source_ids", nonempty=True
    )
    unknown = set(source_ids) - set(source_roles)
    if unknown:
        raise ValidationError(f"{label}.source_ids are not prior sources: {unknown}")
    if not any(source_roles[item] == "user" for item in source_ids):
        raise ValidationError(f"{label} needs a user source or adoption")


def _validate_control(
    value,
    label,
    expected_kind,
    path,
    symbol,
    allowed_check_ids,
    required_check_ids,
):
    _require_keys(value, CONTROL_KEYS, label)
    _require_string(value["control_id"], f"{label}.control_id")
    if value["kind"] != expected_kind:
        raise ValidationError(f"{label}.kind must be {expected_kind}")
    patch = _require_string(value["patch"], f"{label}.patch")
    parse_response(fenced_response(path, patch), path, symbol)
    failing = _require_string_list(
        value["expected_failing_check_ids"],
        f"{label}.expected_failing_check_ids",
        nonempty=True,
    )
    failing_ids = set(failing)
    if not failing_ids <= set(allowed_check_ids):
        raise ValidationError(f"{label} names a check that is not currently active")
    if not failing_ids & set(required_check_ids):
        raise ValidationError(f"{label} lacks its required discriminator kind")


def validate_document(document):
    """Validate one exact canonical authored object and return it unchanged."""
    _require_keys(document, TOP_KEYS, "document")
    if (
        type(document["schema_version"]) is not int
        or document["schema_version"] != SCHEMA_VERSION
    ):
        raise ValidationError("schema_version must be 1")
    if document["split"] != "dev":
        raise ValidationError("split must be dev")
    _require_keys(document["author"], AUTHOR_KEYS, "author")
    if document["author"] != {"name": "kimi", "model": "kimi-k3:cloud"}:
        raise ValidationError("author identity must match the frozen contract")
    _require_keys(document["lineage"], LINEAGE_KEYS, "lineage")
    expected_lineage = {
        "fit_on": "none",
        "development_on": "new original specification-authored coding episode",
        "evaluated_on": "none",
    }
    if document["lineage"] != expected_lineage:
        raise ValidationError("lineage must match the frozen contract")
    episode = document["episode"]
    _require_keys(episode, EPISODE_KEYS, "episode")
    _require_string(episode["episode_id"], "episode.episode_id")
    _require_string(episode["project"], "episode.project")
    task_handles = _require_string_list(
        episode["task_handles"], "episode.task_handles", nonempty=True
    )
    if len(task_handles) != 2:
        raise ValidationError("episode.task_handles must contain exactly two handles")

    initial = episode["initial_file"]
    _require_keys(initial, INITIAL_FILE_KEYS, "episode.initial_file")
    path = _safe_path(initial["path"], "episode.initial_file.path")
    text = _require_string(initial["text"], "episode.initial_file.text")
    if len(text.encode("utf-8")) > MAX_MODULE_BYTES:
        raise ValidationError("initial module exceeds byte limit")
    rounds = _require_sequence(
        episode["rounds"], "episode.rounds", length=EXPECTED_ROUNDS
    )
    for index, round_ in enumerate(rounds):
        _require_keys(round_, ROUND_KEYS, f"rounds[{index}]")
        if type(round_["index"]) is not int or round_["index"] != index:
            raise ValidationError(f"rounds[{index}].index must equal {index}")
        _require_keys(round_["target"], TARGET_KEYS, f"rounds[{index}].target")
        if round_["target"]["path"] != path:
            raise ValidationError(
                f"rounds[{index}] target path must match initial file"
            )
        _safe_symbol(round_["target"]["symbol"], f"rounds[{index}].target.symbol")
    target_symbols = {round_["target"]["symbol"] for round_ in rounds}
    if len(target_symbols) != 3:
        raise ValidationError("six rounds must edit exactly three target functions")

    initial_tree = _parse_python(text, "episode.initial_file.text")
    try:
        compile(text, f"<{path}>", "exec")
    except (SyntaxError, ValueError, OverflowError) as exc:
        raise ValidationError(f"initial module does not compile: {exc}") from exc
    top = list(initial_tree.body)
    if top and isinstance(top[0], ast.Expr) and isinstance(
        top[0].value, ast.Constant
    ) and isinstance(top[0].value.value, str):
        top.pop(0)
    if len(top) != 4 or not all(isinstance(node, ast.FunctionDef) for node in top):
        raise ValidationError("initial module needs one helper and three target stubs")
    by_name = {node.name: node for node in top}
    if len(by_name) != 4 or not target_symbols <= set(by_name):
        raise ValidationError("initial module target definitions do not match rounds")
    for node in top:
        _validate_function(node, node.name, f"initial function {node.name}")
    if not all(_is_none_stub(by_name[name]) for name in target_symbols):
        raise ValidationError("all three target functions must initially return None")
    helpers = set(by_name) - target_symbols
    helper = next(iter(helpers))
    if _is_none_stub(by_name[helper]):
        raise ValidationError("the untouched helper must be implemented")

    initial_checks = _require_sequence(
        episode["initial_checks"], "episode.initial_checks", minimum=1
    )
    for index, check in enumerate(initial_checks):
        _validate_check(check, f"initial_checks[{index}]", set(by_name))
    if not any(check["symbol"] == helper for check in initial_checks):
        raise ValidationError("an initial check must exercise the untouched helper")

    message_ids = set()
    check_ids = set()
    control_ids = set()
    source_roles = {}
    known_rules = {}
    seen_effective_rule_ids = set()

    def unique(identifier, seen, label):
        if identifier in seen:
            raise ValidationError(f"duplicate {label}: {identifier}")
        seen.add(identifier)

    for check in initial_checks:
        unique(check["check_id"], check_ids, "check_id")
    active_functional_ids = {check["check_id"] for check in initial_checks}

    prior_targets = set()
    for index, round_ in enumerate(rounds):
        label = f"rounds[{index}]"
        messages = _require_sequence(
            round_["source_messages"], f"{label}.source_messages", minimum=1
        )
        for offset, message in enumerate(messages):
            mlabel = f"{label}.source_messages[{offset}]"
            _require_keys(message, MESSAGE_KEYS, mlabel)
            mid = _require_string(message["message_id"], f"{mlabel}.message_id")
            unique(mid, message_ids, "message_id")
            if message["role"] not in SOURCE_ROLES:
                raise ValidationError(f"{mlabel}.role must be user or assistant")
            _require_string(message["text"], f"{mlabel}.text")
            source_roles[mid] = message["role"]

        request = round_["request"]
        _require_keys(request, REQUEST_KEYS, f"{label}.request")
        rid = _require_string(request["message_id"], f"{label}.request.message_id")
        unique(rid, message_ids, "message_id")
        if request["role"] != "user":
            raise ValidationError(f"{label}.request.role must be user")
        if request["task_handle"] not in task_handles:
            raise ValidationError(f"{label}.request.task_handle is undeclared")
        _require_string(request["text"], f"{label}.request.text")
        source_roles[rid] = "user"
        _require_string(round_["manual_recap"], f"{label}.manual_recap")

        oracle = round_["oracle"]
        _require_keys(oracle, ORACLE_KEYS, f"{label}.oracle")
        effective = _require_sequence(
            oracle["effective_rules"], f"{label}.oracle.effective_rules", minimum=1
        )
        effective_ids = []
        for offset, rule in enumerate(effective):
            rlabel = f"{label}.oracle.effective_rules[{offset}]"
            _validate_rule(rule, rlabel, task_handles, source_roles)
            rule_id = rule["rule_id"]
            if rule_id in effective_ids:
                raise ValidationError(f"{label} repeats effective rule {rule_id}")
            if rule["scope"] not in {None, request["task_handle"]}:
                raise ValidationError(f"{rlabel} is not applicable to this request")
            # Stable IDs mechanically retain scope and strength.  The prose may
            # restate the same rule or mention a currently active exception;
            # semantic identity of those descriptions is a data-review duty.
            identity = (rule["scope"], rule["strength"])
            if rule_id in known_rules and known_rules[rule_id] != identity:
                raise ValidationError(f"rule {rule_id} changed meaning")
            known_rules[rule_id] = identity
            seen_effective_rule_ids.add(rule_id)
            effective_ids.append(rule_id)
        inactive = _require_string_list(
            oracle["inactive_rule_ids"], f"{label}.oracle.inactive_rule_ids"
        )
        if set(inactive) & set(effective_ids):
            raise ValidationError(f"{label} rule cannot be active and inactive")
        if not set(inactive) <= seen_effective_rule_ids:
            raise ValidationError(f"{label} names an unknown inactive rule")

        symbol = round_["target"]["symbol"]
        reference = _require_string(
            round_["reference_patch"], f"{label}.reference_patch"
        )
        reference_parsed = parse_response(
            fenced_response(path, reference), path, symbol
        )
        reference_node = _parse_single_function(
            reference_parsed.code, symbol, f"{label}.reference_patch"
        )
        functional = _require_sequence(
            round_["functional_checks"],
            f"{label}.functional_checks",
            minimum=2,
        )
        obligations = _require_sequence(
            round_["obligation_checks"],
            f"{label}.obligation_checks",
            minimum=2,
        )
        for offset, check in enumerate(functional):
            _validate_check(check, f"{label}.functional_checks[{offset}]", set(by_name))
            unique(check["check_id"], check_ids, "check_id")
            active_functional_ids.add(check["check_id"])
        for offset, check in enumerate(obligations):
            _validate_check(
                check,
                f"{label}.obligation_checks[{offset}]",
                set(by_name),
                obligation=True,
            )
            unique(check["check_id"], check_ids, "check_id")
            if check["symbol"] != symbol:
                raise ValidationError(f"{label} obligation check must target {symbol}")
            if not set(check["rule_ids"]) <= set(effective_ids):
                raise ValidationError(f"{label} obligation check names inactive rules")

        controls = _require_sequence(
            round_["negative_controls"],
            f"{label}.negative_controls",
            length=2,
        )
        by_kind = {}
        for control in controls:
            if type(control) is not dict:
                raise ValidationError(f"{label}.negative_controls must be objects")
            kind = control.get("kind")
            if kind in by_kind:
                raise ValidationError(f"{label} repeats negative kind {kind}")
            by_kind[kind] = control
        if set(by_kind) != {"functional", "obligation"}:
            raise ValidationError(f"{label} needs functional and obligation controls")
        _validate_control(
            by_kind["functional"],
            f"{label}.negative_controls[functional]",
            "functional",
            path,
            symbol,
            active_functional_ids
            | {check["check_id"] for check in obligations},
            active_functional_ids,
        )
        _validate_control(
            by_kind["obligation"],
            f"{label}.negative_controls[obligation]",
            "obligation",
            path,
            symbol,
            {check["check_id"] for check in obligations},
            {check["check_id"] for check in obligations},
        )
        for control in controls:
            unique(control["control_id"], control_ids, "control_id")

        if index == EXPECTED_ROUNDS - 1:
            calls = {
                child.func.id
                for child in ast.walk(reference_node)
                if isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
            }
            if not calls & (prior_targets - {symbol}):
                raise ValidationError(
                    "last reference patch must call an earlier target function"
                )
        prior_targets.add(symbol)
    return document


def validate_bank(documents):
    if len(documents) not in {1, EXPECTED_EPISODES}:
        raise ValidationError("preflight accepts one episode or exactly four episodes")
    for document in documents:
        validate_document(document)
    episode_ids = [item["episode"]["episode_id"] for item in documents]
    if len(set(episode_ids)) != len(episode_ids):
        raise ValidationError("episode IDs must be unique")
    return documents


def _read_documents(path):
    path = Path(path)
    body = path.read_bytes()
    parsed = json.loads(body)
    values = parsed if type(parsed) is list else [parsed]
    if not values:
        raise ValidationError("combined input list must not be empty")
    return values, {"path": str(path), "bytes": len(body), "sha256": sha256_bytes(body)}


def load_inputs(paths):
    documents = []
    receipts = []
    for path in paths:
        values, receipt = _read_documents(path)
        documents.extend(values)
        receipt["documents"] = len(values)
        receipts.append(receipt)
    return validate_bank(documents), receipts


def _fresh_execute(module_text, symbol, value):
    if len(module_text.encode("utf-8")) > MAX_MODULE_BYTES:
        raise slab.InvalidProgram("resource bound")
    cases_json = compact([[symbol, value]])
    # Bypass the legacy result cache: the contract requires a new seccomp child
    # for every check, including repeated cumulative checks.
    values = slab._execute_cached.__wrapped__(module_text, cases_json)
    if type(values) is not list or len(values) != 1:
        raise slab.InvalidProgram("sandbox returned invalid value count")
    return values[0]


def run_checks(module_text, checks):
    results = []
    for check in checks:
        started = time.monotonic()
        actual = None
        error = None
        passed = False
        try:
            actual = _fresh_execute(module_text, check["symbol"], check["input"])
            passed = any(
                json_equal(actual, expected) for expected in check["expected_values"]
            )
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
        results.append(
            {
                "check_id": check["check_id"],
                "symbol": check["symbol"],
                "rule_ids": list(check["rule_ids"]),
                "passed": passed,
                "actual": actual,
                "expected_values": check["expected_values"],
                "error": error,
                "elapsed_seconds": time.monotonic() - started,
            }
        )
    return results


def _all_pass(results):
    return bool(results) and all(item["passed"] for item in results)


def _active_checks(episode, index):
    stable = list(episode["initial_checks"])
    for round_ in episode["rounds"][: index + 1]:
        stable.extend(round_["functional_checks"])
    obligations = list(episode["rounds"][index]["obligation_checks"])
    return stable, obligations


def preflight_document(document, *, encode=None):
    validate_document(document)
    encode = slab.qwen_encode if encode is None else encode
    episode = document["episode"]
    path = episode["initial_file"]["path"]
    state = episode["initial_file"]["text"]
    started = time.monotonic()
    initial_results = run_checks(state, episode["initial_checks"])
    errors = [
        f"initial check failed: {item['check_id']}"
        for item in initial_results
        if not item["passed"]
    ]
    rounds = []
    for index, round_ in enumerate(episode["rounds"]):
        symbol = round_["target"]["symbol"]
        before = state
        parsed, state = consume_patch(
            before, path, symbol, round_["reference_patch"]
        )
        stable, obligations = _active_checks(episode, index)
        reference_checks = run_checks(state, stable + obligations)
        reference_failures = [
            item["check_id"] for item in reference_checks if not item["passed"]
        ]
        if reference_failures:
            errors.append(f"round {index} reference failed: {reference_failures}")

        controls = []
        stable_ids = {check["check_id"] for check in stable}
        obligation_ids = {check["check_id"] for check in obligations}
        for control in round_["negative_controls"]:
            mutant_parsed, mutant_state = consume_patch(
                before, path, symbol, control["patch"]
            )
            check_results = run_checks(mutant_state, stable + obligations)
            by_id = {item["check_id"]: item for item in check_results}
            named_failed = all(
                not by_id[item]["passed"]
                for item in control["expected_failing_check_ids"]
            )
            stable_passed = all(by_id[item]["passed"] for item in stable_ids)
            obligation_passed = all(
                by_id[item]["passed"] for item in obligation_ids
            )
            valid = named_failed
            if control["kind"] == "obligation":
                valid = valid and stable_passed
            if not valid:
                errors.append(
                    f"round {index} control failed audit: {control['control_id']}"
                )
            controls.append(
                {
                    "control_id": control["control_id"],
                    "kind": control["kind"],
                    "patch_sha256": sha256_text(mutant_parsed.code),
                    "expected_failing_check_ids": control[
                        "expected_failing_check_ids"
                    ],
                    "named_checks_failed": named_failed,
                    "stable_functionality_passed": stable_passed,
                    "current_obligations_passed": obligation_passed,
                    "valid": valid,
                    "checks": check_results,
                }
            )

        counterfactual = fenced_response(
            path, round_["reference_patch"], round_["manual_recap"]
        )
        token_error = None
        reference_tokens = None
        try:
            reference_tokens = len(tuple(encode(counterfactual)))
        except Exception as exc:
            token_error = f"{type(exc).__name__}: {exc}"
            errors.append(f"round {index} tokenizer failed: {token_error}")
        headroom = (
            GENERATION_CAP - reference_tokens
            if reference_tokens is not None
            else None
        )
        sizing_eligible = headroom is not None and headroom >= MIN_GENERATION_HEADROOM
        if not sizing_eligible and token_error is None:
            errors.append(
                f"round {index} reference headroom {headroom} < "
                f"{MIN_GENERATION_HEADROOM}"
            )
        rounds.append(
            {
                "index": index,
                "target": dict(round_["target"]),
                "pre_module_sha256": sha256_text(before),
                "post_module_sha256": sha256_text(state),
                "reference_patch_sha256": sha256_text(parsed.code),
                "reference_checks": reference_checks,
                "reference_passed": _all_pass(reference_checks),
                "negative_controls": controls,
                "counterfactual_reference_sizing": {
                    "actual_http_prompt": False,
                    "description": (
                        "manual recap plus reference fence; actual own-history "
                        "worker requests are unknowable before inference"
                    ),
                    "response_sha256": sha256_text(counterfactual),
                    "tokens_without_eos": reference_tokens,
                    "generation_cap": GENERATION_CAP,
                    "headroom_tokens": headroom,
                    "minimum_headroom_tokens": MIN_GENERATION_HEADROOM,
                    "eligible": sizing_eligible,
                    "error": token_error,
                },
            }
        )
    return {
        "episode_id": episode["episode_id"],
        "eligible": not errors,
        "errors": errors,
        "initial_module_sha256": sha256_text(episode["initial_file"]["text"]),
        "initial_checks": initial_results,
        "rounds": rounds,
        "final_module_sha256": sha256_text(state),
        "elapsed_seconds": time.monotonic() - started,
    }


def preflight_paths(paths, *, encode=None):
    started = time.monotonic()
    inputs = []
    raw_documents = []
    input_errors = []
    for path in paths:
        try:
            values, receipt = _read_documents(path)
            receipt["documents"] = len(values)
            inputs.append(receipt)
            raw_documents.extend(values)
        except Exception as exc:
            input_errors.append(
                {"path": str(path), "error": f"{type(exc).__name__}: {exc}"}
            )
    episode_results = []
    valid_documents = []
    for offset, document in enumerate(raw_documents):
        try:
            validate_document(document)
            valid_documents.append(document)
            episode_results.append(preflight_document(document, encode=encode))
        except Exception as exc:
            episode_id = None
            if isinstance(document, dict) and isinstance(document.get("episode"), dict):
                episode_id = document["episode"].get("episode_id")
            episode_results.append(
                {
                    "episode_id": episode_id,
                    "document_index": offset,
                    "eligible": False,
                    "errors": [f"{type(exc).__name__}: {exc}"],
                    "rounds": [],
                }
            )
    bank_error = None
    try:
        validate_bank(valid_documents)
        if len(valid_documents) != len(raw_documents):
            raise ValidationError("one or more authored documents are invalid")
    except Exception as exc:
        bank_error = f"{type(exc).__name__}: {exc}"
    code_paths = [
        Path(__file__).resolve(),
        Path(slab.__file__).with_name("slab_sandbox.py"),
    ]
    report = {
        "schema_version": 1,
        "kind": "coding-self-cue-cpu-preflight",
        "status": (
            "ELIGIBLE"
            if not input_errors
            and bank_error is None
            and episode_results
            and all(item["eligible"] for item in episode_results)
            else "INELIGIBLE"
        ),
        "actual_http_prompts": 0,
        "model_calls": 0,
        "gpu_used": False,
        "inputs": inputs,
        "input_errors": input_errors,
        "bank_error": bank_error,
        "episode_count": len(raw_documents),
        "scope": "individual" if len(raw_documents) == 1 else "combined",
        "episodes": episode_results,
        "runtime": {
            "fresh_seccomp_process_per_check": True,
            "generation_cap": GENERATION_CAP,
            "minimum_generation_headroom": MIN_GENERATION_HEADROOM,
            "elapsed_seconds": time.monotonic() - started,
        },
        "code_sha256": {
            str(path.relative_to(Path(__file__).resolve().parents[1])): sha256_bytes(
                path.read_bytes()
            )
            for path in code_paths
        },
    }
    return report


def _parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        action="append",
        required=True,
        help="Individual authored JSON or a JSON list; repeat for four authors.",
    )
    parser.add_argument("--output", required=True, type=Path)
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    report = preflight_paths(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": report["status"], "output": str(args.output)}))
    return 0 if report["status"] == "ELIGIBLE" else 2


if __name__ == "__main__":
    sys.exit(main())
