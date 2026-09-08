#!/usr/bin/env python3
"""CPU validator and executable preflight for coding-competence DEV data."""

import argparse
import ast
import copy
import hashlib
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path

try:
    from scripts import coding_worker_dev as cpu
except ModuleNotFoundError as exc:  # Direct ``python scripts/...`` invocation.
    if exc.name != "scripts":
        raise
    import coding_worker_dev as cpu

SCHEMA_VERSION = 1
EXPECTED_EPISODES = 4
EXPECTED_ROUNDS = 3
GENERATION_CAP = 1024
MIN_GENERATION_HEADROOM = 128
MAX_SOURCE_BYTES = 65_536

TOP_KEYS = {"schema_version", "split", "author", "lineage", "public", "private"}
PUBLIC_KEYS = {
    "episode_id",
    "project",
    "task_handles",
    "initial_file",
    "initial_checks",
    "rounds",
}
PRIVATE_KEYS = {"rounds"}
INITIAL_FILE_KEYS = {"path", "text"}
PUBLIC_ROUND_KEYS = {
    "index",
    "source_messages",
    "request",
    "target",
    "public_checks",
}
PRIVATE_ROUND_KEYS = {
    "index",
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
CHECK_KEYS = {"check_id", "symbol", "input", "expected_values", "rule_ids"}
CONTROL_KEYS = {"control_id", "kind", "patch", "expected_failing_check_ids"}
RULE_STRENGTHS = {"required", "prohibited", "permitted", "optional"}
SOURCE_ROLES = {"user", "assistant"}

REPLACE_FUNCTION_TOOL = {
    "type": "function",
    "function": {
        "name": "replace_function",
        "description": "Replace the authenticated current target function.",
        "parameters": {
            "type": "object",
            "properties": {
                "source": {"type": "string"}
            },
            "required": ["source"],
            "additionalProperties": False,
        },
    },
}
FORCED_TOOL_CHOICE = {
    "type": "function",
    "function": {"name": "replace_function"},
}

ValidationError = cpu.ValidationError
PatchError = cpu.PatchError


@dataclass(frozen=True)
class AppliedAction:
    source: str
    source_sha256: str
    module: str
    module_sha256: str


def sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def sha256_text(value):
    return sha256_bytes(value.encode("utf-8"))


def _unique(identifier, seen, label):
    if identifier in seen:
        raise ValidationError(f"duplicate {label}: {identifier}")
    seen.add(identifier)


def _top_functions(module_text):
    tree = cpu._parse_python(module_text, "public.initial_file.text")
    try:
        compile(module_text, "<public initial module>", "exec")
    except (SyntaxError, ValueError, OverflowError) as exc:
        raise ValidationError(f"public initial module does not compile: {exc}") from exc
    nodes = list(tree.body)
    if (
        nodes
        and isinstance(nodes[0], ast.Expr)
        and isinstance(nodes[0].value, ast.Constant)
        and isinstance(nodes[0].value.value, str)
    ):
        nodes.pop(0)
    if len(nodes) < 4 or not all(isinstance(node, ast.FunctionDef) for node in nodes):
        raise ValidationError(
            "initial module needs helpers and exactly three target functions"
        )
    by_name = {}
    for node in nodes:
        cpu._validate_function(node, node.name, f"initial function {node.name}")
        if node.name in by_name:
            raise ValidationError(f"duplicate initial function: {node.name}")
        by_name[node.name] = node
    return by_name


def _validate_check(value, label, symbols, *, obligation=False):
    cpu._require_keys(value, CHECK_KEYS, label)
    cpu._require_string(value["check_id"], f"{label}.check_id")
    symbol = cpu._safe_symbol(value["symbol"], f"{label}.symbol")
    if symbol not in symbols:
        raise ValidationError(f"{label}.symbol is absent from the module")
    cpu._require_json(value["input"], f"{label}.input")
    expected = cpu._require_sequence(
        value["expected_values"], f"{label}.expected_values", minimum=1
    )
    for index, item in enumerate(expected):
        cpu._require_json(item, f"{label}.expected_values[{index}]")
    if any(
        cpu.json_equal(expected[left], expected[right])
        for left in range(len(expected))
        for right in range(left + 1, len(expected))
    ):
        raise ValidationError(f"{label}.expected_values contains duplicates")
    rule_ids = cpu._require_string_list(value["rule_ids"], f"{label}.rule_ids")
    if obligation and not rule_ids:
        raise ValidationError(f"{label}.rule_ids must identify current rules")
    if not obligation and rule_ids:
        raise ValidationError(f"{label}.rule_ids must be empty for functionality")


def _same_case(left, right):
    return left["symbol"] == right["symbol"] and cpu.json_equal(
        left["input"], right["input"]
    )


def _same_expected(left, right):
    if len(left) != len(right):
        return False
    return all(
        any(cpu.json_equal(item, candidate) for candidate in right) for item in left
    )


def _validate_rule(rule, label, task_handles, source_roles):
    cpu._require_keys(rule, RULE_KEYS, label)
    cpu._require_string(rule["rule_id"], f"{label}.rule_id")
    if rule["scope"] not in {"global", *task_handles}:
        raise ValidationError(f"{label}.scope must be global or a task handle")
    if rule["strength"] not in RULE_STRENGTHS:
        raise ValidationError(f"{label}.strength is invalid")
    cpu._require_string(rule["text"], f"{label}.text")
    source_ids = cpu._require_string_list(
        rule["source_ids"], f"{label}.source_ids", nonempty=True
    )
    unknown = set(source_ids) - set(source_roles)
    if unknown:
        raise ValidationError(
            f"{label}.source_ids are not visible antecedents: {unknown}"
        )
    if not any(source_roles[source_id] == "user" for source_id in source_ids):
        raise ValidationError(f"{label} needs a genuine user source or adoption")


def _calls_prior_function(source, available):
    node = cpu._parse_single_function(source, ast.parse(source).body[0].name, "patch")
    calls = {
        child.func.id
        for child in ast.walk(node)
        if isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
    }
    return bool(calls & set(available))


def consume_action(module_text, path, symbol, arguments):
    """Apply exact native tool arguments without source normalization or repair."""
    if type(arguments) is not dict or set(arguments) != {"source"}:
        raise PatchError("replace_function arguments must contain exactly source")
    source = arguments["source"]
    if type(source) is not str or not source.strip():
        raise PatchError("replace_function source must be a nonempty string")
    if not source.startswith("def "):
        raise PatchError("replace_function source must begin with def at byte zero")
    try:
        encoded = source.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise PatchError(
            "replace_function source must contain Unicode scalars"
        ) from exc
    if len(encoded) > MAX_SOURCE_BYTES:
        raise PatchError("replace_function source exceeds byte limit")
    if "\r" in source or "```" in source or "~~~" in source:
        raise PatchError("replace_function source must be unfenced LF Python")
    merged = cpu.splice_function(module_text, source, symbol)
    return AppliedAction(
        source=source,
        source_sha256=sha256_bytes(encoded),
        module=merged,
        module_sha256=sha256_text(merged),
    )


def public_projection(document):
    """Return the only authored document subtree eligible for model visibility."""
    validate_document(document)
    return copy.deepcopy(document["public"])


def current_reminder(document, round_index):
    """Return only the current ephemeral manual reminder, never other private data."""
    validate_document(document)
    if type(round_index) is not int or not 0 <= round_index < EXPECTED_ROUNDS:
        raise IndexError("round index is out of range")
    return {
        "episode_id": document["public"]["episode_id"],
        "round_index": round_index,
        "text": document["private"]["rounds"][round_index]["manual_recap"],
    }


def active_check_sets(document, round_index):
    public = document["public"]
    private = document["private"]
    initial = list(public["initial_checks"])
    cumulative_public = []
    cumulative_private = []
    for index in range(round_index + 1):
        cumulative_public.extend(public["rounds"][index]["public_checks"])
        cumulative_private.extend(private["rounds"][index]["functional_checks"])
    current_obligations = list(private["rounds"][round_index]["obligation_checks"])
    return {
        "initial": initial,
        "cumulative_public": cumulative_public,
        "cumulative_private": cumulative_private,
        "current_obligations": current_obligations,
    }


def validate_document(document):
    """Validate one exact authored public/private competence document."""
    cpu._require_keys(document, TOP_KEYS, "document")
    if type(document["schema_version"]) is not int or document["schema_version"] != 1:
        raise ValidationError("schema_version must be 1")
    if document["split"] != "dev":
        raise ValidationError("split must be dev")
    cpu._require_keys(document["author"], {"name", "model"}, "author")
    if document["author"] != {"name": "kimi", "model": "kimi-k3:cloud"}:
        raise ValidationError("author identity must match the frozen contract")
    cpu._require_keys(
        document["lineage"], {"fit_on", "development_on", "evaluated_on"}, "lineage"
    )
    if document["lineage"] != {
        "fit_on": "none",
        "development_on": "new original coding competence DEV",
        "evaluated_on": "none",
    }:
        raise ValidationError("lineage must match the frozen contract")

    public = document["public"]
    private = document["private"]
    cpu._require_keys(public, PUBLIC_KEYS, "public")
    cpu._require_keys(private, PRIVATE_KEYS, "private")
    cpu._require_string(public["episode_id"], "public.episode_id")
    cpu._require_string(public["project"], "public.project")
    task_handles = cpu._require_string_list(
        public["task_handles"], "public.task_handles", nonempty=True
    )
    initial = public["initial_file"]
    cpu._require_keys(initial, INITIAL_FILE_KEYS, "public.initial_file")
    path = cpu._safe_path(initial["path"], "public.initial_file.path")
    text = cpu._require_string(initial["text"], "public.initial_file.text")
    if len(text.encode("utf-8")) > cpu.MAX_MODULE_BYTES:
        raise ValidationError("initial module exceeds byte limit")

    public_rounds = cpu._require_sequence(
        public["rounds"], "public.rounds", length=EXPECTED_ROUNDS
    )
    private_rounds = cpu._require_sequence(
        private["rounds"], "private.rounds", length=EXPECTED_ROUNDS
    )
    target_symbols = []
    for index, (public_round, private_round) in enumerate(
        zip(public_rounds, private_rounds, strict=True)
    ):
        cpu._require_keys(public_round, PUBLIC_ROUND_KEYS, f"public.rounds[{index}]")
        cpu._require_keys(
            private_round, PRIVATE_ROUND_KEYS, f"private.rounds[{index}]"
        )
        if public_round["index"] != index or type(public_round["index"]) is not int:
            raise ValidationError(f"public.rounds[{index}].index must equal {index}")
        if private_round["index"] != index or type(private_round["index"]) is not int:
            raise ValidationError(f"private.rounds[{index}].index must equal {index}")
        cpu._require_keys(public_round["target"], TARGET_KEYS, f"round {index} target")
        if public_round["target"]["path"] != path:
            raise ValidationError(f"public.rounds[{index}] target path must match")
        target_symbols.append(
            cpu._safe_symbol(
                public_round["target"]["symbol"],
                f"public.rounds[{index}].target.symbol",
            )
        )
    if len(set(target_symbols)) != EXPECTED_ROUNDS:
        raise ValidationError("the three rounds must target distinct functions")

    functions = _top_functions(text)
    if not set(target_symbols) <= set(functions):
        raise ValidationError("target definitions are absent from the initial module")
    if not all(cpu._is_none_stub(functions[symbol]) for symbol in target_symbols):
        raise ValidationError("all three target functions must initially return None")
    helpers = set(functions) - set(target_symbols)
    if not helpers or any(cpu._is_none_stub(functions[symbol]) for symbol in helpers):
        raise ValidationError("initial helper functions must be implemented")

    check_ids = set()
    message_ids = set()
    control_ids = set()
    source_roles = {}
    known_rules = {}
    seen_rule_ids = set()
    public_cases = []
    private_cases = []
    initial_checks = cpu._require_sequence(
        public["initial_checks"], "public.initial_checks", minimum=2
    )
    for offset, check in enumerate(initial_checks):
        label = f"public.initial_checks[{offset}]"
        _validate_check(check, label, functions)
        if check["symbol"] not in helpers:
            raise ValidationError(f"{label} must exercise an initial helper")
        _unique(check["check_id"], check_ids, "check_id")
        public_cases.append(check)
    cumulative_private = []
    available_dependencies = set(helpers)
    for index, (public_round, private_round) in enumerate(
        zip(public_rounds, private_rounds, strict=True)
    ):
        label = f"rounds[{index}]"
        messages = cpu._require_sequence(
            public_round["source_messages"],
            f"public.{label}.source_messages",
        )
        for offset, message in enumerate(messages):
            mlabel = f"public.{label}.source_messages[{offset}]"
            cpu._require_keys(message, MESSAGE_KEYS, mlabel)
            message_id = cpu._require_string(
                message["message_id"], f"{mlabel}.message_id"
            )
            _unique(message_id, message_ids, "message_id")
            if message["role"] not in SOURCE_ROLES:
                raise ValidationError(f"{mlabel}.role must be user or assistant")
            cpu._require_string(message["text"], f"{mlabel}.text")
            source_roles[message_id] = message["role"]
        request = public_round["request"]
        cpu._require_keys(request, REQUEST_KEYS, f"public.{label}.request")
        request_id = cpu._require_string(
            request["message_id"], f"public.{label}.request.message_id"
        )
        _unique(request_id, message_ids, "message_id")
        if request["role"] != "user":
            raise ValidationError(f"public.{label}.request.role must be user")
        if request["task_handle"] not in task_handles:
            raise ValidationError(f"public.{label}.request task handle is undeclared")
        cpu._require_string(request["text"], f"public.{label}.request.text")
        source_roles[request_id] = "user"

        symbol = public_round["target"]["symbol"]
        public_checks = cpu._require_sequence(
            public_round["public_checks"], f"public.{label}.public_checks", minimum=2
        )
        for offset, check in enumerate(public_checks):
            clabel = f"public.{label}.public_checks[{offset}]"
            _validate_check(check, clabel, functions)
            if check["symbol"] != symbol:
                raise ValidationError(f"{clabel} must target {symbol}")
            _unique(check["check_id"], check_ids, "check_id")
            public_cases.append(check)

        cpu._require_string(
            private_round["manual_recap"], f"private.{label}.manual_recap"
        )
        oracle = private_round["oracle"]
        cpu._require_keys(oracle, ORACLE_KEYS, f"private.{label}.oracle")
        effective = cpu._require_sequence(
            oracle["effective_rules"],
            f"private.{label}.oracle.effective_rules",
            minimum=1,
        )
        effective_ids = []
        for offset, rule in enumerate(effective):
            rlabel = f"private.{label}.oracle.effective_rules[{offset}]"
            _validate_rule(rule, rlabel, task_handles, source_roles)
            rule_id = rule["rule_id"]
            if rule_id in effective_ids:
                raise ValidationError(
                    f"private.{label} repeats effective rule {rule_id}"
                )
            identity = (rule["scope"], rule["strength"], rule["text"])
            if rule_id in known_rules and known_rules[rule_id] != identity:
                raise ValidationError(f"rule {rule_id} changed identity")
            known_rules[rule_id] = identity
            seen_rule_ids.add(rule_id)
            effective_ids.append(rule_id)
        inactive = cpu._require_string_list(
            oracle["inactive_rule_ids"],
            f"private.{label}.oracle.inactive_rule_ids",
        )
        if set(inactive) & set(effective_ids):
            raise ValidationError(f"private.{label} rule cannot be active and inactive")
        if not set(inactive) <= seen_rule_ids:
            raise ValidationError(f"private.{label} names an unknown inactive rule")

        reference = cpu._require_string(
            private_round["reference_patch"], f"private.{label}.reference_patch"
        )
        consume_action(text, path, symbol, {"source": reference})
        if not _calls_prior_function(reference, available_dependencies):
            raise ValidationError(f"private.{label}.reference_patch lacks a dependency")
        available_dependencies.add(symbol)

        functional = cpu._require_sequence(
            private_round["functional_checks"],
            f"private.{label}.functional_checks",
            minimum=2,
        )
        obligations = cpu._require_sequence(
            private_round["obligation_checks"],
            f"private.{label}.obligation_checks",
            minimum=2,
        )
        for kind, checks in (("functional", functional), ("obligation", obligations)):
            for offset, check in enumerate(checks):
                clabel = f"private.{label}.{kind}_checks[{offset}]"
                _validate_check(
                    check, clabel, functions, obligation=kind == "obligation"
                )
                if check["symbol"] != symbol:
                    raise ValidationError(f"{clabel} must target {symbol}")
                if kind == "obligation" and not set(check["rule_ids"]) <= set(
                    effective_ids
                ):
                    raise ValidationError(f"{clabel} names an inapplicable rule")
                _unique(check["check_id"], check_ids, "check_id")
                private_cases.append(check)
        cumulative_private.extend(functional)
        for left in cumulative_private:
            for right in obligations:
                if _same_case(left, right) and not _same_expected(
                    left["expected_values"], right["expected_values"]
                ):
                    raise ValidationError(
                        f"private.{label} gives inconsistent outputs for one input"
                    )

        controls = cpu._require_sequence(
            private_round["negative_controls"],
            f"private.{label}.negative_controls",
            length=2,
        )
        by_kind = {}
        active_functional_ids = {check["check_id"] for check in cumulative_private}
        obligation_ids = {check["check_id"] for check in obligations}
        for offset, control in enumerate(controls):
            clabel = f"private.{label}.negative_controls[{offset}]"
            cpu._require_keys(control, CONTROL_KEYS, clabel)
            control_id = cpu._require_string(
                control["control_id"], f"{clabel}.control_id"
            )
            _unique(control_id, control_ids, "control_id")
            kind = control["kind"]
            if kind not in {"functional", "obligation"} or kind in by_kind:
                raise ValidationError(f"private.{label} needs one control of each kind")
            by_kind[kind] = control
            patch = cpu._require_string(control["patch"], f"{clabel}.patch")
            consume_action(text, path, symbol, {"source": patch})
            if patch == reference:
                raise ValidationError(f"{clabel}.patch must differ from the reference")
            failing = cpu._require_string_list(
                control["expected_failing_check_ids"],
                f"{clabel}.expected_failing_check_ids",
                nonempty=True,
            )
            failing_ids = set(failing)
            if not failing_ids <= active_functional_ids | obligation_ids:
                raise ValidationError(f"{clabel} names a non-active private check")
            discriminator_ids = (
                active_functional_ids if kind == "functional" else obligation_ids
            )
            if not failing_ids & discriminator_ids:
                raise ValidationError(
                    f"{clabel} lacks a {kind} private discriminator"
                )
        if set(by_kind) != {"functional", "obligation"}:
            raise ValidationError(
                f"private.{label} needs functional and obligation controls"
            )

    for hidden in private_cases:
        if any(_same_case(hidden, visible) for visible in public_cases):
            raise ValidationError(
                f"private check {hidden['check_id']} reuses a public symbol/input pair"
            )
    return document


def validate_bank(documents):
    if len(documents) not in {1, EXPECTED_EPISODES}:
        raise ValidationError("preflight accepts one episode or exactly four episodes")
    for document in documents:
        validate_document(document)
    episode_ids = [document["public"]["episode_id"] for document in documents]
    if len(set(episode_ids)) != len(episode_ids):
        raise ValidationError("episode IDs must be unique")
    return documents


def _read_documents(path):
    path = Path(path)
    receipt = {
        "path": str(path),
        "bytes": None,
        "sha256": None,
        "documents": None,
        "read_error": None,
        "parse_error": None,
    }
    try:
        body = path.read_bytes()
    except Exception as exc:
        receipt["read_error"] = f"{type(exc).__name__}: {exc}"
        return None, receipt
    receipt["bytes"] = len(body)
    receipt["sha256"] = sha256_bytes(body)
    try:
        parsed = json.loads(body)
    except Exception as exc:
        receipt["parse_error"] = f"{type(exc).__name__}: {exc}"
        return None, receipt
    values = parsed if type(parsed) is list else [parsed]
    if not values:
        receipt["parse_error"] = "ValidationError: input document list is empty"
        return None, receipt
    receipt["documents"] = len(values)
    return values, receipt


def load_inputs(paths):
    documents = []
    receipts = []
    for path in paths:
        values, receipt = _read_documents(path)
        receipts.append(receipt)
        if values is not None:
            documents.extend(values)
    input_errors = [
        receipt["read_error"] or receipt["parse_error"]
        for receipt in receipts
        if receipt["read_error"] or receipt["parse_error"]
    ]
    if input_errors:
        error = ValidationError(f"input read/parse failures: {input_errors}")
        error.input_receipts = receipts
        raise error
    try:
        validated = validate_bank(documents)
    except Exception as exc:
        exc.input_receipts = receipts
        raise
    return validated, receipts


def _run_check_group(module_text, episode_id, checks):
    results = cpu.run_checks(module_text, checks)
    module_sha256 = sha256_text(module_text)
    for check, result in zip(checks, results, strict=True):
        result["episode_id"] = episode_id
        result["input"] = copy.deepcopy(check["input"])
        result["module_sha256"] = module_sha256
        result["check_sha256"] = sha256_text(
            json.dumps(
                check,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        )
    return results


def _all_pass(results):
    return bool(results) and all(result["passed"] for result in results)


def _audit_control(document, before, round_index, control):
    public = document["public"]
    target = public["rounds"][round_index]["target"]
    applied = consume_action(
        before, target["path"], target["symbol"], {"source": control["patch"]}
    )
    groups = active_check_sets(document, round_index)
    results = {
        name: _run_check_group(
            applied.module, public["episode_id"], checks
        )
        for name, checks in groups.items()
    }
    by_id = {
        result["check_id"]: result
        for group in results.values()
        for result in group
    }
    named_failed = all(
        check_id in by_id and not by_id[check_id]["passed"]
        for check_id in control["expected_failing_check_ids"]
    )
    stable_private_passed = _all_pass(results["cumulative_private"])
    valid = named_failed
    if control["kind"] == "obligation":
        valid = valid and stable_private_passed
    return {
        "control_id": control["control_id"],
        "kind": control["kind"],
        "source_sha256": applied.source_sha256,
        "module_sha256": applied.module_sha256,
        "expected_failing_check_ids": list(control["expected_failing_check_ids"]),
        "named_checks_failed": named_failed,
        "stable_private_functionality_passed": stable_private_passed,
        "failed_public_check_ids": [
            result["check_id"]
            for name in ("initial", "cumulative_public")
            for result in results[name]
            if not result["passed"]
        ],
        "failed_current_obligation_ids": [
            result["check_id"]
            for result in results["current_obligations"]
            if not result["passed"]
        ],
        "valid": valid,
        "checks": results,
    }


def preflight_document(document):
    validate_document(document)
    public = document["public"]
    private = document["private"]
    episode_id = public["episode_id"]
    state = public["initial_file"]["text"]
    errors = []
    initial_results = _run_check_group(state, episode_id, public["initial_checks"])
    for result in initial_results:
        if not result["passed"]:
            errors.append(f"initial check failed: {result['check_id']}")
    rounds = []
    for index, (public_round, private_round) in enumerate(
        zip(public["rounds"], private["rounds"], strict=True)
    ):
        before = state
        target = public_round["target"]
        reference = consume_action(
            before,
            target["path"],
            target["symbol"],
            {"source": private_round["reference_patch"]},
        )
        state = reference.module
        groups = active_check_sets(document, index)
        reference_checks = {
            name: _run_check_group(state, episode_id, checks)
            for name, checks in groups.items()
        }
        reference_failures = [
            result["check_id"]
            for results in reference_checks.values()
            for result in results
            if not result["passed"]
        ]
        if reference_failures:
            errors.append(f"round {index} reference failed: {reference_failures}")
        controls = []
        for control in private_round["negative_controls"]:
            receipt = _audit_control(document, before, index, control)
            if not receipt["valid"]:
                errors.append(
                    f"round {index} control failed audit: {control['control_id']}"
                )
            controls.append(receipt)
        compact_action = json.dumps(
            {"source": private_round["reference_patch"]},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        argument_tokens = len(cpu.slab.qwen_encode(compact_action))
        if argument_tokens + MIN_GENERATION_HEADROOM > GENERATION_CAP:
            errors.append(
                f"round {index} reference argument lacks provisional headroom"
            )
        rounds.append(
            {
                "index": index,
                "target": dict(target),
                "pre_module_sha256": sha256_text(before),
                "post_module_sha256": reference.module_sha256,
                "reference_source_sha256": reference.source_sha256,
                "reference_argument_tokens": argument_tokens,
                "provisional_generation_headroom": GENERATION_CAP - argument_tokens,
                "reference_checks": reference_checks,
                "reference_failures": reference_failures,
                "controls": controls,
            }
        )
    execution_count = len(initial_results) + sum(
        sum(len(results) for results in round_["reference_checks"].values())
        + sum(
            sum(len(results) for results in control["checks"].values())
            for control in round_["controls"]
        )
        for round_ in rounds
    )
    return {
        "schema_version": 1,
        "episode_id": episode_id,
        "valid": not errors,
        "errors": errors,
        "initial_checks": initial_results,
        "rounds": rounds,
        "final_module_sha256": sha256_text(state),
        "execution_count": execution_count,
        "public_rule_invariance": "requires independent semantic source review",
    }


def _code_hashes():
    root = Path(__file__).resolve().parents[1]
    paths = {
        Path(__file__).resolve(),
        Path(cpu.__file__).resolve(),
        Path(cpu.slab.__file__).resolve(),
        Path(cpu.slab.__file__).with_name("slab_sandbox.py").resolve(),
    }
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(paths, key=str)
    }


def preflight_inputs(paths):
    started = time.monotonic()
    documents, inputs = load_inputs(paths)
    try:
        episodes = [preflight_document(document) for document in documents]
    except Exception as exc:
        exc.input_receipts = inputs
        raise
    return {
        "schema_version": 1,
        "kind": "coding-competence-cpu-preflight",
        "model_calls": 0,
        "status": "PASS" if all(episode["valid"] for episode in episodes) else "FAIL",
        "inputs": inputs,
        "code_sha256": _code_hashes(),
        "documents": len(documents),
        "episodes": episodes,
        "execution_count": sum(episode["execution_count"] for episode in episodes),
        "elapsed_seconds": time.monotonic() - started,
    }


def _parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", action="append", required=True)
    parser.add_argument("--output", type=Path)
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    started = time.monotonic()
    try:
        result = preflight_inputs(args.input)
    except Exception as exc:
        result = {
            "schema_version": 1,
            "kind": "coding-competence-cpu-preflight",
            "model_calls": 0,
            "status": "INVALID",
            "error": f"{type(exc).__name__}: {exc}",
            "inputs": getattr(exc, "input_receipts", []),
            "code_sha256": _code_hashes(),
            "elapsed_seconds": time.monotonic() - started,
        }
    body = json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as handle:
            handle.write(body)
    print(json.dumps(result, ensure_ascii=True, sort_keys=True), flush=True)
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
