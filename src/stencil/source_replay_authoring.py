"""Strict staged assembly for prospective source-replay project authoring."""

import copy
import json
from string import Template

from scripts import coding_competence_dev as action
from stencil import source_replay_screen as screen

SCAFFOLD_FIELDS = {"description", "lineage", "initial_source", "rounds"}
SCAFFOLD_ROUND_FIELDS = {"source_texts", "target_symbol"}
ASSEMBLED_SCAFFOLD_FIELDS = {"project_id", "description", "initial_file", "rounds"}
ASSEMBLED_ROUND_FIELDS = {"index", "source_messages", "request", "target"}
PACKET_FIELDS = {"reference_patch", "public_checks", "private_checks"}
FINAL_PACKET_FIELDS = {*PACKET_FIELDS, "obsolete_mutant"}
REQUEST_TEMPLATE = (
    "Update {symbol} in module.py to implement the latest changes described in our "
    "conversation while preserving all still-applicable behavior."
)


class StageValidationError(ValueError):
    """A stage failed after producing execution evidence."""

    def __init__(self, message, record):
        super().__init__(message)
        self.record = copy.deepcopy(record)


class StageExecutionInterrupted(RuntimeError):
    """A deadline interrupted validation after zero or more recorded cases."""

    def __init__(self, message, record):
        super().__init__(message)
        self.record = copy.deepcopy(record)


class _DeadlineInterrupted(RuntimeError):
    pass


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _constant(value):
    raise ValueError(f"nonfinite JSON number: {value}")


def parse_author_json(body):
    """Parse one complete strict JSON object without repair or fence removal."""
    if isinstance(body, bytes):
        try:
            text = body.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"author response is not UTF-8: {exc}") from exc
    elif isinstance(body, str):
        text = body
    else:
        raise ValueError("author response must be bytes or text")
    try:
        value = json.loads(
            text,
            object_pairs_hook=_pairs,
            parse_constant=_constant,
        )
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError(
            f"author response is not one strict JSON value: {exc}"
        ) from exc
    if type(value) is not dict:
        raise ValueError("author response must be one JSON object")
    return value


def _json(value):
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def render_scaffold_prompt(template_text, project_id, domain):
    """Render the accepted template once; inserted dollar markers stay literal."""
    return Template(template_text).substitute(
        project_id=_json(project_id),
        domain=_json(domain),
    )


def render_round_prompt(
    template_text,
    project_id,
    round_index,
    scaffold,
    prior_packets,
    data_contract,
):
    """Render one packet request from immutable accepted artifacts."""
    if type(round_index) is not int or round_index not in {1, 2, 3}:
        raise ValueError("round_index must be 1, 2 or 3")
    return Template(template_text).substitute(
        project_id=_json(project_id),
        round_index=str(round_index),
        scaffold=_json(scaffold),
        prior_packets=_json(prior_packets),
        data_contract=data_contract,
    )


def request_text(symbol):
    return REQUEST_TEMPLATE.format(symbol=symbol)


def _object(value, fields, label):
    if type(value) is not dict or set(value) != fields:
        raise ValueError(f"{label} has the wrong fields")
    return value


def _text(value, label):
    return screen._text(value, label)


def _message(identifier, text):
    return {"message_id": identifier, "role": "user", "text": text}


def validate_scaffold_response(value):
    """Validate stage 0 before deterministic administrative assembly."""
    _object(value, SCAFFOLD_FIELDS, "scaffold response")
    result = copy.deepcopy(value)
    _text(result["description"], "description")
    _text(result["lineage"], "lineage")
    symbols = screen._module_symbols(
        {"path": "module.py", "text": result["initial_source"]}
    )
    rounds = result["rounds"]
    if type(rounds) is not list or len(rounds) != 3:
        raise ValueError("scaffold rounds must contain exactly three items")
    targets = []
    for index, round_ in enumerate(rounds):
        _object(round_, SCAFFOLD_ROUND_FIELDS, f"rounds[{index}]")
        sources = round_["source_texts"]
        if type(sources) is not list or len(sources) != 4:
            raise ValueError("each scaffold round needs exactly four source texts")
        for source_index, text in enumerate(sources):
            _text(text, f"rounds[{index}].source_texts[{source_index}]")
            if len(text.encode("utf-8")) > 640:
                raise ValueError("source text exceeds 640 UTF-8 bytes")
        symbol = _text(round_["target_symbol"], f"rounds[{index}].target_symbol")
        if symbol not in symbols:
            raise ValueError("scaffold target is absent from the initial module")
        targets.append(symbol)
    if len(set(targets)) == len(targets):
        raise ValueError("at least one scaffold target must be revisited")
    return result


def assemble_scaffold(project_id, authored):
    """Add only the fixed path, IDs, roles, indices, and request template."""
    _text(project_id, "project_id")
    authored = validate_scaffold_response(authored)
    rounds = []
    for offset, round_ in enumerate(authored["rounds"]):
        first = offset * 5 + 1
        symbol = round_["target_symbol"]
        rounds.append(
            {
                "index": offset + 1,
                "source_messages": [
                    _message(f"m{first + index:02d}", text)
                    for index, text in enumerate(round_["source_texts"])
                ],
                "request": _message(f"m{first + 4:02d}", request_text(symbol)),
                "target": {"path": "module.py", "symbol": symbol},
            }
        )
    scaffold = {
        "project_id": project_id,
        "description": authored["description"],
        "initial_file": {"path": "module.py", "text": authored["initial_source"]},
        "rounds": rounds,
    }
    validate_scaffold(scaffold)
    return scaffold, authored["lineage"]


def validate_scaffold(value):
    """Validate the public-only deterministic stage schedule."""
    _object(value, ASSEMBLED_SCAFFOLD_FIELDS, "assembled scaffold")
    result = copy.deepcopy(value)
    _text(result["project_id"], "project_id")
    _text(result["description"], "description")
    symbols = screen._module_symbols(result["initial_file"])
    rounds = result["rounds"]
    if type(rounds) is not list or len(rounds) != 3:
        raise ValueError("assembled scaffold needs exactly three rounds")
    targets = []
    expected_message = 1
    for index, round_ in enumerate(rounds, 1):
        _object(round_, ASSEMBLED_ROUND_FIELDS, f"rounds[{index - 1}]")
        if type(round_["index"]) is not int or round_["index"] != index:
            raise ValueError("assembled round index is invalid")
        sources = round_["source_messages"]
        if type(sources) is not list or len(sources) != 4:
            raise ValueError("assembled round needs four source messages")
        originals = [*sources, round_["request"]]
        for original in originals:
            if type(original) is not dict or set(original) != {
                "message_id",
                "role",
                "text",
            }:
                raise ValueError("assembled original has the wrong fields")
            if original["message_id"] != f"m{expected_message:02d}":
                raise ValueError("assembled message IDs are not sequential")
            if original["role"] != "user":
                raise ValueError("assembled original role must be user")
            _text(original["text"], "assembled original text")
            if len(original["text"].encode("utf-8")) > 640:
                raise ValueError("assembled source/request exceeds 640 UTF-8 bytes")
            expected_message += 1
        target = round_["target"]
        if (
            type(target) is not dict
            or set(target) != {"path", "symbol"}
            or target["path"] != "module.py"
            or target["symbol"] not in symbols
            or round_["request"]["text"] != request_text(target["symbol"])
        ):
            raise ValueError("assembled target/request is invalid")
        targets.append(target["symbol"])
    if len(set(targets)) == len(targets):
        raise ValueError("at least one assembled target must be revisited")
    return result


def _visible_ids(scaffold, round_index):
    return {
        item["message_id"]
        for round_ in scaffold["rounds"][:round_index]
        for item in [*round_["source_messages"], round_["request"]]
    }


def _validate_packet_shape(scaffold, packet, round_index, prior_checks):
    expected = FINAL_PACKET_FIELDS if round_index == 3 else PACKET_FIELDS
    _object(packet, expected, f"round {round_index} packet")
    target = scaffold["rounds"][round_index - 1]["target"]["symbol"]
    screen._single_function(packet["reference_patch"], target, "reference_patch")
    symbols = screen._module_symbols(scaffold["initial_file"])
    visible = _visible_ids(scaffold, round_index)
    current = []
    for name in ("public_checks", "private_checks"):
        checks = packet[name]
        if type(checks) is not list:
            raise ValueError(f"{name} must be a list")
        if name == "private_checks" and len(checks) < 2:
            raise ValueError("each packet needs at least two private checks")
        for index, check in enumerate(checks):
            screen._check(
                check,
                f"round {round_index} {name}[{index}]",
                symbols,
                round_index,
                visible,
            )
            current.append(check)
    if not any(
        item["behavior"] == "functionality" for item in packet["private_checks"]
    ):
        raise ValueError("each packet needs a private functionality check")
    all_checks = [*prior_checks, *current]
    ids = [item["check_id"] for item in all_checks]
    if len(ids) != len(set(ids)):
        raise ValueError("check IDs must be unique across packets")
    for future_round in range(1, 4):
        active = [item for item in all_checks if screen._active(item, future_round)]
        for left in range(len(active)):
            for right in range(left + 1, len(active)):
                one, two = active[left], active[right]
                if one["symbol"] == two["symbol"] and action.cpu.json_equal(
                    one["input"], two["input"]
                ):
                    same = len(one["expected_values"]) == len(
                        two["expected_values"]
                    ) and all(
                        any(
                            action.cpu.json_equal(value, candidate)
                            for candidate in two["expected_values"]
                        )
                        for value in one["expected_values"]
                    )
                    if not same:
                        raise ValueError("conflicting overlapping expected outputs")
    if round_index == 3:
        mutant = packet["obsolete_mutant"]
        if type(mutant) is not dict or set(mutant) != {"source", "failing_check_id"}:
            raise ValueError("obsolete_mutant has the wrong fields")
        screen._single_function(mutant["source"], target, "obsolete_mutant.source")
        _text(mutant["failing_check_id"], "obsolete_mutant.failing_check_id")
    return current


def validate_packet(scaffold, prior_packets, value, round_index):
    """Validate one packet against the immutable scaffold and accepted prefix."""
    scaffold = validate_scaffold(scaffold)
    if type(prior_packets) is not list or len(prior_packets) != round_index - 1:
        raise ValueError("prior_packets must be the exact accepted prefix")
    prior = []
    prior_private = []
    for index, packet in enumerate(prior_packets, 1):
        expected = FINAL_PACKET_FIELDS if index == 3 else PACKET_FIELDS
        _object(packet, expected, f"prior packet {index}")
        for name in ("public_checks", "private_checks"):
            if type(packet[name]) is not list:
                raise ValueError("prior packet checks must be lists")
            prior.extend(packet[name])
        prior_private.extend(packet["private_checks"])
    result = copy.deepcopy(value)
    _validate_packet_shape(scaffold, result, round_index, prior)
    current_private = result["private_checks"]
    active_private = [
        item
        for item in [*prior_private, *current_private]
        if screen._active(item, round_index)
    ]
    retained = [
        item
        for item in active_private
        if item["behavior"] == "retained" or item["active_from_round"] < round_index
    ]
    if len(retained) < 2:
        raise ValueError("current round needs two active private retained cases")
    if (
        round_index >= 2
        and sum(item["behavior"] == "retirement" for item in active_private) < 2
    ):
        raise ValueError("current round needs two active private retirement cases")
    if round_index == 3:
        failing = result["obsolete_mutant"]["failing_check_id"]
        by_id = {item["check_id"]: item for item in active_private}
        if failing not in by_id or by_id[failing]["behavior"] != "retirement":
            raise ValueError("mutant must name an active private retirement check")
    return result


def _active_packet_checks(prior_packets, packet, round_index):
    public = []
    private = []
    for item in [*prior_packets, packet]:
        public.extend(item["public_checks"])
        private.extend(item["private_checks"])
    return (
        [item for item in public if screen._active(item, round_index)],
        [item for item in private if screen._active(item, round_index)],
    )


def _adapt(check):
    return {
        key: copy.deepcopy(check[key]) for key in screen.EXECUTABLE_CHECK_FIELDS
    } | {"rule_ids": []}


def _check_deadline(deadline_check):
    try:
        deadline_check()
    except Exception as exc:
        raise _DeadlineInterrupted(str(exc)) from exc


def _run_each(module, checks, deadline_check, records):
    for check in checks:
        _check_deadline(deadline_check)
        result = action.cpu.run_checks(module, [_adapt(check)])
        for item in result:
            item["input"] = copy.deepcopy(check["input"])
        records.extend(result)
        _check_deadline(deadline_check)


def validate_and_apply_packet(
    scaffold,
    prior_packets,
    value,
    round_index,
    reference_module,
    *,
    deadline_check=lambda: None,
):
    """Validate, apply once, and execute every current active case."""
    packet = validate_packet(scaffold, prior_packets, value, round_index)
    target = scaffold["rounds"][round_index - 1]["target"]
    before = reference_module
    record = {
        "round_index": round_index,
        "target": copy.deepcopy(target),
        "module_before": before,
        "module_before_sha256": action.sha256_text(before),
        "module_after": None,
        "module_after_sha256": None,
        "public_results": [],
        "private_results": [],
        "all_active_checks_passed": False,
        "mutant": None,
    }
    try:
        _check_deadline(deadline_check)
        applied = action.consume_action(
            before,
            target["path"],
            target["symbol"],
            {"source": packet["reference_patch"]},
        )
    except _DeadlineInterrupted as exc:
        raise StageExecutionInterrupted(
            f"stage execution interrupted by deadline: {exc}", record
        ) from exc
    except action.PatchError as exc:
        raise StageValidationError(
            f"reference is not consumable: {exc}", record
        ) from exc
    module = applied.module
    record.update(
        module_after=module,
        module_after_sha256=applied.module_sha256,
        reference_source_sha256=applied.source_sha256,
    )
    public, private = _active_packet_checks(prior_packets, packet, round_index)
    try:
        _run_each(module, public, deadline_check, record["public_results"])
        _run_each(module, private, deadline_check, record["private_results"])
        results = [*record["public_results"], *record["private_results"]]
        record["all_active_checks_passed"] = bool(results) and all(
            item["passed"] for item in results
        )
        if not record["all_active_checks_passed"]:
            raise StageValidationError("reference failed an active check", record)
        if round_index == 3:
            mutant = packet["obsolete_mutant"]
            try:
                mutant_action = action.consume_action(
                    module,
                    target["path"],
                    target["symbol"],
                    {"source": mutant["source"]},
                )
            except action.PatchError as exc:
                raise StageValidationError(
                    f"obsolete mutant is not consumable: {exc}", record
                ) from exc
            failing_id = mutant["failing_check_id"]
            designated = next(
                item for item in private if item["check_id"] == failing_id
            )
            reference_result = next(
                item
                for item in record["private_results"]
                if item["check_id"] == failing_id
            )
            record["mutant"] = {
                "source_sha256": mutant_action.source_sha256,
                "module_sha256": mutant_action.module_sha256,
                "failing_check_id": failing_id,
                "reference_designated_result": reference_result,
                "designated_result": None,
                "results": [],
            }
            _run_each(
                mutant_action.module,
                [designated],
                deadline_check,
                record["mutant"]["results"],
            )
            record["mutant"]["designated_result"] = record["mutant"]["results"][0]
            if (
                reference_result["passed"] is not True
                or record["mutant"]["designated_result"]["passed"] is True
            ):
                raise StageValidationError(
                    "obsolete mutant did not demonstrate the designated retirement",
                    record,
                )
        _check_deadline(deadline_check)
    except _DeadlineInterrupted as exc:
        raise StageExecutionInterrupted(
            f"stage execution interrupted by deadline: {exc}", record
        ) from exc
    return packet, module, record


def assemble_project(scaffold, lineage, packets):
    """Create only the inherited final project schema and validate it exactly."""
    scaffold = validate_scaffold(scaffold)
    _text(lineage, "lineage")
    if type(packets) is not list or len(packets) != 3:
        raise ValueError("assembly needs exactly three accepted packets")
    accepted = []
    for index, packet in enumerate(packets, 1):
        accepted.append(validate_packet(scaffold, accepted, packet, index))
    public_rounds = []
    private_rounds = []
    for index, (round_, packet) in enumerate(
        zip(scaffold["rounds"], accepted, strict=True), 1
    ):
        public_rounds.append(
            {
                **copy.deepcopy(round_),
                "public_checks": copy.deepcopy(packet["public_checks"]),
            }
        )
        private_rounds.append(
            {
                "index": index,
                "reference_patch": packet["reference_patch"],
                "checks": copy.deepcopy(packet["private_checks"]),
            }
        )
    project = {
        "schema_version": 1,
        "author": screen.AUTHOR,
        "lineage": lineage,
        "public": {
            "project_id": scaffold["project_id"],
            "description": scaffold["description"],
            "initial_file": copy.deepcopy(scaffold["initial_file"]),
            "rounds": public_rounds,
        },
        "private": {
            "rounds": private_rounds,
            "obsolete_mutant": copy.deepcopy(accepted[-1]["obsolete_mutant"]),
        },
    }
    return screen.validate_project(project)
