"""Pure contracts and accounting for the bounded source-replay screen."""

import ast
import copy
import math
import re

from scripts import coding_worker_dev as worker
from stencil import source_replay as replay

SCHEMA_VERSION = 1
AUTHOR = "kimi-k3:cloud"
ARMS = ("H", "S", "R")
PROJECTS = 4
ROUNDS = 3
PLANNED_WORKER_CALLS = 36
PLANNED_SELECTOR_CALLS = 12
PLANNED_CALLS = 48
MAX_MODULE_BYTES = 65_536
MAX_REPLACEMENT_BYTES = 65_536
WORKER_CAP = 1024
MIN_REFERENCE_HEADROOM = 128
HISTORICAL_GENERATION_SECONDS = 2041.199447651
CHECK_FIELDS = {
    "check_id",
    "symbol",
    "input",
    "expected_values",
    "active_from_round",
    "active_through_round",
    "source_ids",
    "behavior",
    "rationale",
}
EXECUTABLE_CHECK_FIELDS = {"check_id", "symbol", "input", "expected_values"}
BEHAVIORS = {"functionality", "retained", "retirement"}
SHA256 = re.compile(r"[0-9a-f]{64}")

TOP_FIELDS = {"schema_version", "author", "lineage", "public", "private"}
PUBLIC_FIELDS = {"project_id", "description", "initial_file", "rounds"}
PRIVATE_FIELDS = {"rounds", "obsolete_mutant"}
ROUND_FIELDS = {"index", "source_messages", "request", "target", "public_checks"}
PRIVATE_ROUND_FIELDS = {"index", "reference_patch", "checks"}
FILE_FIELDS = {"path", "text"}
MUTANT_FIELDS = {"source", "failing_check_id"}
BINDING_FIELDS = {"path", "sha256"}
INPUT_FIELDS = {
    "schema_version",
    "kind",
    "projects",
    "source_review",
    "qualification",
}
QUALIFICATION_ROLES = {
    "manifest",
    "lifecycle",
    "terminal",
    "selector_call",
    "worker_call",
    "result_review",
}


def _object(value, fields, label):
    if type(value) is not dict or set(value) != fields:
        raise ValueError(f"{label} has the wrong fields")
    return value


def _text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be nonempty text")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValueError(f"{label} must contain Unicode scalars") from exc
    return value


def _exact_int(value, expected, label):
    if type(value) is not int or value != expected:
        raise ValueError(f"{label} must be {expected}")


def _single_function(source, symbol, label):
    _text(source, label)
    if len(source.encode("utf-8")) > MAX_REPLACEMENT_BYTES:
        raise ValueError(f"{label} exceeds 65536 UTF-8 bytes")
    try:
        node = worker._parse_single_function(source, symbol, label, ValueError)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} is not a safe replacement: {exc}") from exc
    annotations = [node.returns]
    annotations.extend(item.annotation for item in node.args.posonlyargs)
    annotations.extend(item.annotation for item in node.args.args)
    if any(item is not None for item in annotations):
        raise ValueError(f"{label} must not use an annotation")
    return node


def _module_symbols(initial):
    _object(initial, FILE_FIELDS, "public.initial_file")
    if initial["path"] != "module.py":
        raise ValueError("public.initial_file.path must be module.py")
    text = _text(initial["text"], "public.initial_file.text")
    if len(text.encode("utf-8")) > MAX_MODULE_BYTES:
        raise ValueError("public.initial_file.text exceeds 65536 UTF-8 bytes")
    try:
        tree = ast.parse(text)
        compile(text, "<source replay initial module>", "exec")
    except (SyntaxError, ValueError, OverflowError) as exc:
        raise ValueError(f"public.initial_file.text is invalid Python: {exc}") from exc
    nodes = list(tree.body)
    if (
        nodes
        and isinstance(nodes[0], ast.Expr)
        and isinstance(nodes[0].value, ast.Constant)
        and isinstance(nodes[0].value.value, str)
    ):
        nodes.pop(0)
    if not nodes or not all(isinstance(node, ast.FunctionDef) for node in nodes):
        raise ValueError("initial module may contain only top-level functions")
    symbols = set()
    for node in nodes:
        if node.name in symbols:
            raise ValueError(f"duplicate initial function: {node.name}")
        try:
            worker._validate_function(
                node, node.name, f"initial function {node.name}", ValueError
            )
        except (TypeError, ValueError) as exc:
            raise ValueError(f"initial function {node.name} is unsafe: {exc}") from exc
        annotations = [node.returns]
        annotations.extend(item.annotation for item in node.args.posonlyargs)
        annotations.extend(item.annotation for item in node.args.args)
        if any(item is not None for item in annotations):
            raise ValueError(f"initial function {node.name} must not use an annotation")
        symbols.add(node.name)
    return symbols


def _check(value, label, symbols, introduction, visible_ids):
    _object(value, CHECK_FIELDS, label)
    identifier = _text(value["check_id"], f"{label}.check_id")
    symbol = _text(value["symbol"], f"{label}.symbol")
    if symbol not in symbols:
        raise ValueError(f"{label}.symbol is absent from the initial module")
    try:
        replay._json_value(value["input"], f"{label}.input")
        replay._json_value(value["expected_values"], f"{label}.expected_values")
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must contain finite JSON values") from exc
    expected = value["expected_values"]
    if type(expected) is not list or not expected:
        raise ValueError(f"{label}.expected_values must be nonempty")
    if any(
        worker.json_equal(expected[left], expected[right])
        for left in range(len(expected))
        for right in range(left + 1, len(expected))
    ):
        raise ValueError(f"{label}.expected_values contains duplicates")
    _exact_int(value["active_from_round"], introduction, f"{label}.active_from_round")
    through = value["active_through_round"]
    if through is not None and (
        type(through) is not int or through < introduction or through > ROUNDS
    ):
        raise ValueError(f"{label}.active_through_round is invalid")
    sources = value["source_ids"]
    if (
        type(sources) is not list
        or not sources
        or any(not isinstance(item, str) or not item for item in sources)
        or len(sources) != len(set(sources))
        or not set(sources) <= visible_ids
    ):
        raise ValueError(f"{label}.source_ids are not unique visible antecedents")
    if value["behavior"] not in BEHAVIORS:
        raise ValueError(f"{label}.behavior is invalid")
    _text(value["rationale"], f"{label}.rationale")
    return identifier


def _active(check, round_index):
    through = check["active_through_round"]
    return check["active_from_round"] <= round_index and (
        through is None or round_index <= through
    )


def validate_project(value):
    """Validate one exact independently authored three-round project."""
    _object(value, TOP_FIELDS, "project")
    document = copy.deepcopy(value)
    _exact_int(document["schema_version"], SCHEMA_VERSION, "schema_version")
    if document["author"] != AUTHOR:
        raise ValueError(f"author must be {AUTHOR}")
    _text(document["lineage"], "lineage")
    public = _object(document["public"], PUBLIC_FIELDS, "public")
    private = _object(document["private"], PRIVATE_FIELDS, "private")
    _text(public["project_id"], "public.project_id")
    _text(public["description"], "public.description")
    symbols = _module_symbols(public["initial_file"])
    public_rounds = public["rounds"]
    private_rounds = private["rounds"]
    if type(public_rounds) is not list or len(public_rounds) != ROUNDS:
        raise ValueError("public.rounds must contain exactly three rounds")
    if type(private_rounds) is not list or len(private_rounds) != ROUNDS:
        raise ValueError("private.rounds must contain exactly three rounds")

    seen_messages = set()
    seen_checks = set()
    visible_ids = set()
    all_checks = []
    targets = []
    for offset, (public_round, private_round) in enumerate(
        zip(public_rounds, private_rounds, strict=True), 1
    ):
        _object(public_round, ROUND_FIELDS, f"public.rounds[{offset - 1}]")
        _object(private_round, PRIVATE_ROUND_FIELDS, f"private.rounds[{offset - 1}]")
        _exact_int(public_round["index"], offset, "public round index")
        _exact_int(private_round["index"], offset, "private round index")
        sources = replay.validate_originals(public_round["source_messages"])
        if len(sources) != 4:
            raise ValueError(
                "each source_messages list must contain exactly four items"
            )
        request = replay.validate_originals([public_round["request"]])[0]
        originals = [*sources, request]
        expected_ids = [
            f"m{number:02d}" for number in range((offset - 1) * 5 + 1, offset * 5 + 1)
        ]
        if [item["message_id"] for item in originals] != expected_ids:
            raise ValueError(
                "message IDs must be m01 through m15 in conversation order"
            )
        for item in originals:
            if item["message_id"] in seen_messages:
                raise ValueError("message IDs must be globally unique")
            seen_messages.add(item["message_id"])
            visible_ids.add(item["message_id"])
        target = public_round["target"]
        _object(target, replay.TARGET_KEYS, "public target")
        if target["path"] != "module.py" or target["symbol"] not in symbols:
            raise ValueError("target must identify an existing module.py function")
        targets.append(target["symbol"])
        _single_function(
            private_round["reference_patch"],
            target["symbol"],
            f"private.rounds[{offset - 1}].reference_patch",
        )
        for group_name, checks in (
            ("public", public_round["public_checks"]),
            ("private", private_round["checks"]),
        ):
            if type(checks) is not list:
                raise ValueError(f"{group_name} checks must be a list")
            if group_name == "private" and len(checks) < 2:
                raise ValueError("each round must introduce at least two private cases")
            for index, item in enumerate(checks):
                identifier = _check(
                    item,
                    f"{group_name}.rounds[{offset - 1}].checks[{index}]",
                    symbols,
                    offset,
                    visible_ids,
                )
                if identifier in seen_checks:
                    raise ValueError("check IDs must be globally unique")
                seen_checks.add(identifier)
                all_checks.append(item)
        if not any(
            item["behavior"] == "functionality" for item in private_round["checks"]
        ):
            raise ValueError("each round needs a new private functionality case")
    if len(set(targets)) == len(targets):
        raise ValueError("at least one target must be revisited")

    for round_index in range(1, ROUNDS + 1):
        active_private = [
            item
            for private_round in private_rounds
            for item in private_round["checks"]
            if _active(item, round_index)
        ]
        retained = [
            item
            for item in active_private
            if item["behavior"] == "retained" or item["active_from_round"] < round_index
        ]
        if len(retained) < 2:
            raise ValueError(f"round {round_index} needs two active retained cases")
        if (
            round_index >= 2
            and sum(item["behavior"] == "retirement" for item in active_private) < 2
        ):
            raise ValueError(f"round {round_index} needs two active retirement cases")
        active = [item for item in all_checks if _active(item, round_index)]
        for left in range(len(active)):
            for right in range(left + 1, len(active)):
                one, two = active[left], active[right]
                if one["symbol"] == two["symbol"] and worker.json_equal(
                    one["input"], two["input"]
                ):
                    same = len(one["expected_values"]) == len(
                        two["expected_values"]
                    ) and all(
                        any(
                            worker.json_equal(item, candidate)
                            for candidate in two["expected_values"]
                        )
                        for item in one["expected_values"]
                    )
                    if not same:
                        raise ValueError("conflicting active expected outputs")

    mutant = _object(private["obsolete_mutant"], MUTANT_FIELDS, "obsolete_mutant")
    _single_function(mutant["source"], targets[-1], "obsolete_mutant.source")
    failing = _text(mutant["failing_check_id"], "obsolete_mutant.failing_check_id")
    active_final_private = {
        item["check_id"]: item for item in active_checks(document, 3)[1]
    }
    if (
        failing not in active_final_private
        or active_final_private[failing]["behavior"] != "retirement"
    ):
        raise ValueError(
            "obsolete mutant must identify an active private retirement case"
        )
    return document


def active_checks(document, round_index):
    """Return copied active public and private checks at an authored round."""
    if type(round_index) is not int or not 1 <= round_index <= ROUNDS:
        raise ValueError("round_index must be 1, 2 or 3")
    public = [
        copy.deepcopy(item)
        for round_ in document["public"]["rounds"]
        for item in round_["public_checks"]
        if _active(item, round_index)
    ]
    private = [
        copy.deepcopy(item)
        for round_ in document["private"]["rounds"]
        for item in round_["checks"]
        if _active(item, round_index)
    ]
    return public, private


def eligible_originals(document, round_index):
    """Return all originals strictly before the current request."""
    if type(round_index) is not int or not 1 <= round_index <= ROUNDS:
        raise ValueError("round_index must be 1, 2 or 3")
    originals = []
    for round_ in document["public"]["rounds"][:round_index]:
        originals.extend(copy.deepcopy(round_["source_messages"]))
        if round_["index"] < round_index:
            originals.append(copy.deepcopy(round_["request"]))
    return replay.validate_originals(originals)


def recency_originals(document, round_index):
    return eligible_originals(document, round_index)[-replay.MAX_SELECTED_MESSAGES :]


def public_project(document):
    """Project authored content while dropping every private and audit-only field."""
    public = copy.deepcopy(document["public"])
    for round_ in public["rounds"]:
        round_["public_checks"] = [
            {key: copy.deepcopy(item[key]) for key in EXECUTABLE_CHECK_FIELDS}
            for item in round_["public_checks"]
        ]
    return public


def planned_slots(documents):
    """Precompute the exact serial 48-call schedule."""
    if type(documents) is not list or len(documents) != PROJECTS:
        raise ValueError("screen needs exactly four projects")
    slots = []
    for project_index, document in enumerate(documents):
        project_id = document["public"]["project_id"]
        for round_zero in range(ROUNDS):
            offset = (project_index + round_zero) % len(ARMS)
            rotation = ARMS[offset:] + ARMS[:offset]
            for arm in rotation:
                if arm == "S":
                    slots.append(
                        {
                            "slot_index": len(slots),
                            "project_index": project_index,
                            "project_id": project_id,
                            "round_index": round_zero + 1,
                            "arm": arm,
                            "kind": "selector",
                            "status": "UNATTEMPTED",
                        }
                    )
                slots.append(
                    {
                        "slot_index": len(slots),
                        "project_index": project_index,
                        "project_id": project_id,
                        "round_index": round_zero + 1,
                        "arm": arm,
                        "kind": "worker",
                        "status": "UNATTEMPTED",
                    }
                )
    if len(slots) != PLANNED_CALLS:
        raise AssertionError("internal screen schedule is not 48 calls")
    return slots


def projected_seconds(case_executions, max_check_seconds, max_render_seconds):
    values = (case_executions, max_check_seconds, max_render_seconds)
    if any(isinstance(item, bool) or type(item) not in {int, float} for item in values):
        raise ValueError("projection operands must be numeric")
    if any(not math.isfinite(item) or item < 0 for item in values):
        raise ValueError("projection operands must be finite and nonnegative")
    return (
        600
        + HISTORICAL_GENERATION_SECONDS
        + max(
            120,
            case_executions * max_check_seconds
            + PLANNED_CALLS * max_render_seconds
            + 60,
        )
        + 60
    )


def _cost(records, arm, field):
    chosen = [item for item in records if item.get("arm") == arm]
    if field == "tokens":
        return sum(
            item["usage"]["prompt_tokens"] + item["usage"]["completion_tokens"]
            for item in chosen
        )
    return sum(item["http_elapsed_seconds"] for item in chosen)


def evaluate_gate(
    round_records, call_records, intervention_evidence, *, expected_slots=PLANNED_CALLS
):
    """Evaluate only the registered practical screen gate."""
    complete_calls = (
        type(call_records) is list
        and len(call_records) == expected_slots
        and all(item.get("status") == "COMPLETE" for item in call_records)
    )
    keys = {
        (item.get("project_index"), item.get("round_index"), item.get("arm"))
        for item in round_records
    }
    complete_rounds = len(round_records) == PROJECTS * ROUNDS * len(ARMS) and len(
        keys
    ) == len(round_records)
    successes = {
        arm: sum(
            item.get("successful") is True
            for item in round_records
            if item.get("arm") == arm
        )
        for arm in ARMS
    }
    finals = {
        arm: sum(
            item.get("successful") is True
            for item in round_records
            if item.get("arm") == arm and item.get("round_index") == 3
        )
        for arm in ARMS
    }
    by_project = {
        arm: [
            sum(
                item.get("successful") is True
                for item in round_records
                if item.get("arm") == arm and item.get("project_index") == project
            )
            for project in range(PROJECTS)
        ]
        for arm in ARMS
    }
    improved = sum(s > h for s, h in zip(by_project["S"], by_project["H"], strict=True))
    no_losses = all(
        s >= h for s, h in zip(by_project["S"], by_project["H"], strict=True)
    )
    try:
        h_tokens, s_tokens = (
            _cost(call_records, "H", "tokens"),
            _cost(call_records, "S", "tokens"),
        )
        h_http, s_http = (
            _cost(call_records, "H", "http"),
            _cost(call_records, "S", "http"),
        )
        costs_valid = all(
            type(value) in {int, float}
            and not isinstance(value, bool)
            and math.isfinite(value)
            and value >= 0
            for value in (h_tokens, s_tokens, h_http, s_http)
        )
    except (KeyError, TypeError, ValueError):
        h_tokens = s_tokens = h_http = s_http = 0
        costs_valid = False
    no_intervention = (
        type(intervention_evidence) is dict
        and intervention_evidence.get("events") == []
        and intervention_evidence.get("schedule_automatic") is True
        and intervention_evidence.get("manual_action_interface") is False
        and intervention_evidence.get("retries") == 0
        and type(intervention_evidence.get("retries")) is int
        and intervention_evidence.get("actual_requests_recorded") is True
    )
    criteria = {
        "complete_schedule": complete_calls and complete_rounds,
        "s_rounds": successes["S"] >= 9,
        "s_finals": finals["S"] >= 3,
        "gain_over_h": successes["S"] - successes["H"] >= 2,
        "project_improvement": improved >= 2 and no_losses,
        "at_least_r": successes["S"] >= successes["R"],
        "token_cost": costs_valid and h_tokens > 0 and s_tokens <= 2 * h_tokens,
        "http_cost": costs_valid and h_http > 0 and s_http <= 2 * h_http,
        "no_intervention": no_intervention,
    }
    return {
        "disposition": "PASS" if all(criteria.values()) else "FAIL",
        "criteria": criteria,
        "successful_rounds": successes,
        "final_successes": finals,
        "project_successes": by_project,
        "costs": {
            "H": {"tokens": h_tokens, "http_elapsed_seconds": h_http},
            "S": {"tokens": s_tokens, "http_elapsed_seconds": s_http},
        },
    }


def _binding(value, label):
    _object(value, BINDING_FIELDS, label)
    _text(value["path"], f"{label}.path")
    if (
        not isinstance(value["sha256"], str)
        or SHA256.fullmatch(value["sha256"]) is None
    ):
        raise ValueError(f"{label}.sha256 is invalid")


def validate_input_manifest(value):
    """Validate the smallest root-authored screen manifest without reading files."""
    _object(value, INPUT_FIELDS, "screen input")
    result = copy.deepcopy(value)
    _exact_int(result["schema_version"], 1, "screen input schema_version")
    if result["kind"] != "source-replay-screen-input":
        raise ValueError("screen input kind is invalid")
    projects = result["projects"]
    if type(projects) is not list or len(projects) != PROJECTS:
        raise ValueError("screen input must bind exactly four projects")
    for index, value in enumerate(projects):
        _binding(value, f"projects[{index}]")
    paths = [value["path"] for value in projects]
    if len(set(paths)) != len(paths):
        raise ValueError("project paths must be unique")
    _binding(result["source_review"], "source_review")
    qualification = _object(
        result["qualification"], QUALIFICATION_ROLES, "qualification"
    )
    for role in sorted(qualification):
        _binding(qualification[role], f"qualification.{role}")
    return result
