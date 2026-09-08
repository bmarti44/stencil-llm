#!/usr/bin/env python3
"""Run the bounded two-call native source-replay qualification."""

import argparse
import base64
import copy
import json
import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import coding_competence_dev as cpu  # noqa: E402
from scripts import coding_competence_run as native  # noqa: E402
from stencil import source_replay as replay  # noqa: E402
from stencil.focus.native_source_selector import (  # noqa: E402
    NativeSourceSelectorClient,
)

SCHEMA_VERSION = 1
AUTHOR = "kimi-k3:cloud"
PAIR_DEADLINE_SECONDS = 181.0
DEFAULT_DEADLINE_SECONDS = 540.0
PREFLIGHT_FILENAME = "qualification-preflight.json"
MIN_REFERENCE_HEADROOM = 128
PREFLIGHT_CODE_FILES = (
    "scripts/source_replay_qualification.py",
    "src/stencil/source_replay.py",
    "src/stencil/focus/native_source_selector.py",
    "scripts/coding_competence_run.py",
    "scripts/coding_competence_dev.py",
    "scripts/coding_worker_dev.py",
    "src/stencil/focus/slab.py",
    "src/stencil/focus/slab_sandbox.py",
)
TOP_KEYS = {
    "schema_version",
    "author",
    "lineage",
    "initial_file",
    "source_messages",
    "request",
    "target",
    "reference_patch",
    "checks",
}
FILE_KEYS = {"path", "text"}
CHECK_KEYS = {"check_id", "symbol", "input", "expected_values"}

_sha_bytes = native._sha_bytes


def _read_fixture(path):
    path = Path(path)
    try:
        body = path.read_bytes()
        value = json.loads(body)
    except Exception as exc:
        raise ValueError(f"fixture is not readable JSON: {exc}") from exc
    return validate_fixture(value), {
        "path": str(path.resolve()),
        "bytes": len(body),
        "sha256": _sha_bytes(body),
    }


def _read_json(path, label):
    try:
        return json.loads(Path(path).read_bytes())
    except Exception as exc:
        raise ValueError(f"{label} is not readable JSON: {exc}") from exc


def _code_hashes():
    return {
        relative: _sha_bytes((ROOT / relative).read_bytes())
        for relative in PREFLIGHT_CODE_FILES
    }


def _check(value, label, target_symbol):
    if type(value) is not dict or set(value) != CHECK_KEYS:
        raise ValueError(f"{label} has the wrong fields")
    if not isinstance(value["check_id"], str) or not value["check_id"]:
        raise ValueError(f"{label}.check_id must be nonempty text")
    if value["symbol"] != target_symbol:
        raise ValueError(f"{label}.symbol must equal the target symbol")
    if type(value["expected_values"]) is not list or not value["expected_values"]:
        raise ValueError(f"{label}.expected_values must be a nonempty list")
    try:
        replay.canonical_json(value["input"])
        replay.canonical_json(value["expected_values"])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must contain finite JSON values") from exc


def _adapt_checks(checks):
    return [dict(copy.deepcopy(check), rule_ids=[]) for check in checks]


def validate_fixture(value):
    """Fail closed on the tiny, independently authored fixture contract."""
    if type(value) is not dict or set(value) != TOP_KEYS:
        raise ValueError("fixture has the wrong top-level fields")
    fixture = copy.deepcopy(value)
    if type(fixture["schema_version"]) is not int or fixture["schema_version"] != 1:
        raise ValueError("fixture schema_version must be 1")
    if fixture["author"] != AUTHOR:
        raise ValueError(f"fixture author must be {AUTHOR}")
    if not isinstance(fixture["lineage"], str) or not fixture["lineage"].strip():
        raise ValueError("fixture lineage must be nonempty prose")

    initial = fixture["initial_file"]
    if type(initial) is not dict or set(initial) != FILE_KEYS:
        raise ValueError("initial_file must contain exactly path and text")
    target = fixture["target"]
    if type(target) is not dict or set(target) != replay.TARGET_KEYS:
        raise ValueError("target must contain exactly path and symbol")
    if initial["path"] != "module.py" or target["path"] != initial["path"]:
        raise ValueError("fixture target must identify module.py")
    if not isinstance(initial["text"], str) or not initial["text"]:
        raise ValueError("initial_file.text must be nonempty text")
    symbol = target["symbol"]
    if not isinstance(symbol, str) or not symbol:
        raise ValueError("target.symbol must be nonempty text")
    try:
        initial_node = cpu.cpu._parse_single_function(
            initial["text"], symbol, "initial_file.text", ValueError
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(f"initial_file.text is not one safe function: {exc}") from exc

    if initial_node.returns is not None or any(
        argument.annotation is not None
        for argument in (*initial_node.args.posonlyargs, *initial_node.args.args)
    ):
        raise ValueError("initial_file.text must not use annotations")

    if fixture["source_messages"] == []:
        raise ValueError("source_messages must contain exactly one m01 message")
    sources = replay.validate_originals(fixture["source_messages"])
    if len(sources) != 1 or sources[0]["message_id"] != "m01":
        raise ValueError("source_messages must contain exactly one m01 message")
    request = replay.validate_originals([fixture["request"]])[0]
    if request["message_id"] != "m02":
        raise ValueError("request message_id must be m02")

    reference = fixture["reference_patch"]
    if not isinstance(reference, str) or not reference:
        raise ValueError("reference_patch must be nonempty text")
    try:
        reference_node = cpu.cpu._parse_single_function(
            reference, symbol, "reference_patch", ValueError
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(f"reference_patch is not one safe function: {exc}") from exc
    if reference_node.returns is not None or any(
        argument.annotation is not None
        for argument in (*reference_node.args.posonlyargs, *reference_node.args.args)
    ):
        raise ValueError("reference_patch must not use annotations")

    checks = fixture["checks"]
    if type(checks) is not list or len(checks) < 2:
        raise ValueError("checks must contain at least two cases")
    seen = set()
    for index, check in enumerate(checks):
        _check(check, f"checks[{index}]", symbol)
        if check["check_id"] in seen:
            raise ValueError("check IDs must be unique")
        seen.add(check["check_id"])
    return fixture


def preflight_fixture(input_path, token_counter, tokenizer_identity):
    """Run the exact CPU consumer once and measure exact native argument bytes."""
    fixture, input_receipt = _read_fixture(input_path)
    if type(tokenizer_identity) is not dict or set(tokenizer_identity) != {
        "name",
        "path",
        "sha256",
    }:
        raise ValueError("tokenizer_identity has the wrong fields")
    tokenizer_path = Path(tokenizer_identity["path"])
    if (
        not isinstance(tokenizer_identity["name"], str)
        or not tokenizer_identity["name"]
        or not tokenizer_path.is_file()
        or tokenizer_identity["sha256"] != _sha_bytes(tokenizer_path.read_bytes())
    ):
        raise ValueError("tokenizer_identity does not bind an existing tokenizer")
    initial = fixture["initial_file"]
    target = fixture["target"]
    try:
        action = cpu.consume_action(
            initial["text"],
            initial["path"],
            target["symbol"],
            {"source": fixture["reference_patch"]},
        )
    except cpu.PatchError as exc:
        raise ValueError(f"reference_patch is not consumable: {exc}") from exc
    checks = cpu.cpu.run_checks(action.module, _adapt_checks(fixture["checks"]))
    argument_body = native._json_bytes({"source": fixture["reference_patch"]})
    argument_tokens = token_counter(argument_body.decode("utf-8"))
    if type(argument_tokens) is not int or argument_tokens < 0:
        raise ValueError("token_counter must return a nonnegative integer")
    response_tokens = argument_tokens + 1
    headroom = native.MAX_OUTPUT_TOKENS - response_tokens
    checks_passed = bool(checks) and all(item["passed"] for item in checks)
    eligible = checks_passed and headroom >= MIN_REFERENCE_HEADROOM
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": "source-replay-qualification-cpu-preflight",
        "status": "PASS" if eligible else "INELIGIBLE",
        "model_calls": 0,
        "input": input_receipt,
        "consumer_code_sha256": _code_hashes(),
        "tokenizer": copy.deepcopy(tokenizer_identity),
        "reference_action": {
            "argument_body": argument_body.decode("utf-8"),
            "argument_body_base64": base64.b64encode(argument_body).decode("ascii"),
            "argument_body_bytes": len(argument_body),
            "argument_body_sha256": _sha_bytes(argument_body),
            "source_sha256": action.source_sha256,
            "module_sha256": action.module_sha256,
            "argument_tokens": argument_tokens,
            "eos_allowance_tokens": 1,
            "response_tokens_with_eos": response_tokens,
            "generation_headroom": headroom,
            "eligible": headroom >= MIN_REFERENCE_HEADROOM,
        },
        "checks": checks,
        "all_reference_checks_passed": checks_passed,
    }


def _validate_preflight(path, fixture, input_receipt):
    preflight = _read_json(path, "qualification preflight")
    if (
        type(preflight) is not dict
        or type(preflight.get("schema_version")) is not int
        or preflight.get("schema_version") != SCHEMA_VERSION
        or preflight.get("kind") != "source-replay-qualification-cpu-preflight"
        or preflight.get("status") != "PASS"
        or type(preflight.get("model_calls")) is not int
        or preflight.get("model_calls") != 0
        or preflight.get("all_reference_checks_passed") is not True
        or preflight.get("consumer_code_sha256") != _code_hashes()
    ):
        raise ValueError("qualification CPU preflight is not current and passing")
    recorded_input = preflight.get("input")
    if (
        type(recorded_input) is not dict
        or recorded_input.get("bytes") != input_receipt["bytes"]
        or recorded_input.get("sha256") != input_receipt["sha256"]
        or Path(recorded_input.get("path", "")).resolve()
        != Path(input_receipt["path"]).resolve()
    ):
        raise ValueError("qualification CPU preflight is for a different fixture")
    tokenizer = preflight.get("tokenizer")
    if type(tokenizer) is not dict or set(tokenizer) != {"name", "path", "sha256"}:
        raise ValueError("qualification CPU preflight lacks tokenizer identity")
    tokenizer_path = Path(tokenizer["path"])
    if (
        not tokenizer_path.is_file()
        or _sha_bytes(tokenizer_path.read_bytes()) != tokenizer["sha256"]
    ):
        raise ValueError("qualification CPU preflight tokenizer changed")
    action = preflight.get("reference_action")
    expected_body = native._json_bytes({"source": fixture["reference_patch"]})
    if (
        type(action) is not dict
        or action.get("argument_body") != expected_body.decode("utf-8")
        or action.get("argument_body_base64")
        != base64.b64encode(expected_body).decode("ascii")
        or action.get("argument_body_bytes") != len(expected_body)
        or action.get("argument_body_sha256") != _sha_bytes(expected_body)
        or action.get("source_sha256") != native._sha_text(fixture["reference_patch"])
        or type(action.get("argument_tokens")) is not int
        or action.get("eos_allowance_tokens") != 1
        or action.get("response_tokens_with_eos") != action["argument_tokens"] + 1
        or action.get("generation_headroom")
        != native.MAX_OUTPUT_TOKENS - action["response_tokens_with_eos"]
        or action.get("generation_headroom") < MIN_REFERENCE_HEADROOM
        or action.get("eligible") is not True
    ):
        raise ValueError("qualification CPU preflight action is ineligible")
    results = preflight.get("checks")
    if (
        type(results) is not list
        or [item.get("check_id") for item in results if type(item) is dict]
        != [item["check_id"] for item in fixture["checks"]]
        or any(
            type(item) is not dict or item.get("passed") is not True for item in results
        )
    ):
        raise ValueError("qualification CPU preflight check receipt is incomplete")
    return preflight


def _prepare_output(path):
    path = Path(path)
    if path.exists() and (not path.is_dir() or any(path.iterdir())):
        raise FileExistsError("qualification output directory is nonempty")
    path.mkdir(parents=True, exist_ok=True)
    calls = path / "calls"
    workspaces = path / "workspaces"
    calls.mkdir(exist_ok=False)
    workspaces.mkdir(exist_ok=False)
    records = []
    for index, kind in enumerate(("selector", "worker")):
        record = {
            "schema_version": SCHEMA_VERSION,
            "index": index,
            "kind": kind,
            "status": "UNATTEMPTED",
            "request": None,
            "deadline_monotonic": None,
            "exchange": None,
            "result": None,
            "error": None,
        }
        native._write_json(calls / f"call-{index:04d}.json", record, exclusive=True)
        records.append(record)
    return path, records


def _save_call(output, record):
    native._write_json(output / "calls" / f"call-{record['index']:04d}.json", record)


def _request_record(body):
    return {
        "body": body.decode("utf-8"),
        "body_base64": base64.b64encode(body).decode("ascii"),
        "body_bytes": len(body),
        "body_sha256": _sha_bytes(body),
    }


def _set_pair_deadline(client, global_deadline, clock):
    now = clock()
    if now >= global_deadline:
        raise native.TechnicalError("deadline", "global driver deadline expired")
    pair_deadline = min(global_deadline, now + PAIR_DEADLINE_SECONDS)
    client.set_deadline(pair_deadline)
    return pair_deadline


def _perform_call(client, messages, record, output, global_deadline, clock, manifest):
    pair_deadline = _set_pair_deadline(client, global_deadline, clock)
    try:
        body = native._json_bytes(client.payload(messages))
    except Exception as exc:
        raise native.TechnicalError(
            "local_request", f"request serialization failed: {native._error(exc)}"
        ) from exc
    record.update(
        status="PENDING",
        request=_request_record(body),
        deadline_monotonic=pair_deadline,
    )
    _save_call(output, record)

    def persist(exchange):
        record["exchange"] = copy.deepcopy(exchange)
        _save_call(output, record)

    try:
        manifest["model_calls"] += 1
        native._write_json(output / "manifest.json", manifest)
        result = client.perform(body, persist)
        if clock() >= pair_deadline or clock() >= global_deadline:
            raise native.TechnicalError(
                "deadline", "native pair returned after its shared deadline"
            )
    except native.TechnicalError as exc:
        record.update(
            status="ERROR",
            error={"kind": exc.kind, "message": str(exc)},
        )
        _save_call(output, record)
        raise
    record.update(status="PENDING_FINALIZATION", result=copy.deepcopy(result))
    _save_call(output, record)
    if clock() >= pair_deadline or clock() >= global_deadline:
        exc = native.TechnicalError(
            "deadline", "native pair receipt crossed its shared deadline"
        )
        record.update(status="ERROR", error={"kind": exc.kind, "message": str(exc)})
        _save_call(output, record)
        raise exc
    record["status"] = "COMPLETE"
    _save_call(output, record)
    if clock() >= pair_deadline or clock() >= global_deadline:
        exc = native.TechnicalError(
            "deadline", "native pair final call publication was late"
        )
        record.update(status="ERROR", error={"kind": exc.kind, "message": str(exc)})
        _save_call(output, record)
        raise exc
    return result


def _tool_feedback(call_id, applied):
    value = {
        "action_status": "applied",
        "current_module": {"path": "module.py", "text": applied.module},
        "public_checks": [],
    }
    return {
        "role": "tool",
        "tool_call_id": call_id,
        "name": "replace_function",
        "content": replay.canonical_json(value),
    }


def _base_manifest(input_receipt, started, deadline):
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": "source-replay-native-qualification",
        "status": "IN_PROGRESS",
        "technical_eligible": False,
        "behavior_passed": None,
        "input": input_receipt,
        "started_monotonic": started,
        "deadline_monotonic": deadline,
        "ended_monotonic": None,
        "selected_source_ids": None,
        "evidence_message": None,
        "issued_messages": None,
        "permanent_history": None,
        "check_results": None,
        "technical_failure": None,
        "consumer_failure": None,
        "model_calls": 0,
    }


def _incomplete(manifest, output, exc, clock):
    manifest.update(
        status="INCOMPLETE",
        technical_eligible=False,
        ended_monotonic=clock(),
        technical_failure={"kind": exc.kind, "message": str(exc)},
    )
    native._write_json(output / "manifest.json", manifest)
    return manifest


def run_qualification(
    input_path,
    output_dir,
    selector_client=None,
    worker_client=None,
    *,
    deadline_seconds=DEFAULT_DEADLINE_SECONDS,
    clock=time.monotonic,
):
    """Execute exactly one selector call followed by one worker call."""
    if (
        isinstance(deadline_seconds, bool)
        or type(deadline_seconds) not in {int, float}
        or not math.isfinite(deadline_seconds)
        or deadline_seconds <= 0
    ):
        raise ValueError("deadline_seconds must be positive and finite")
    started = clock()
    deadline = started + deadline_seconds
    fixture, input_receipt = _read_fixture(input_path)
    preflight_path = Path(input_path).with_name(PREFLIGHT_FILENAME)
    preflight = _validate_preflight(preflight_path, fixture, input_receipt)
    output, records = _prepare_output(output_dir)
    manifest = _base_manifest(input_receipt, started, deadline)
    native._write_json(output / "manifest.json", manifest, exclusive=True)
    if clock() >= deadline:
        return _incomplete(
            manifest,
            output,
            native.TechnicalError("deadline", "qualification setup was late"),
            clock,
        )

    initial = fixture["initial_file"]
    target = fixture["target"]
    native._write_json(output / "preflight.json", preflight, exclusive=True)
    native._write_text(output / "workspaces" / "before.py", initial["text"])

    source_ids = [item["message_id"] for item in fixture["source_messages"]]
    if selector_client is None:
        selector_client = NativeSourceSelectorClient(
            "http://127.0.0.1:18088", "/model", source_ids
        )
    if worker_client is None:
        worker_client = native.NativeToolClient("http://127.0.0.1:18088", "/model")

    selector_messages = replay.build_selector_messages(
        fixture["source_messages"], fixture["request"]
    )
    try:
        selector_result = _perform_call(
            selector_client,
            selector_messages,
            records[0],
            output,
            deadline,
            clock,
            manifest,
        )
        try:
            selected_ids = selector_result["arguments"]["source_ids"]
            evidence = replay.render_evidence(fixture["source_messages"], selected_ids)
            records[0]["consumer"] = {
                "status": "ACCEPTED",
                "selected_source_ids": list(selected_ids),
            }
            _save_call(output, records[0])
            if clock() >= deadline:
                raise native.TechnicalError(
                    "deadline", "selector consumer receipt publication was late"
                )
        except (KeyError, TypeError, ValueError) as exc:
            raise native.TechnicalError(
                "source_consumer", f"selector output was not consumable: {exc}"
            ) from exc
    except native.TechnicalError as exc:
        return _incomplete(manifest, output, exc, clock)

    history = [
        {"role": "system", "content": native.SYSTEM_PROMPT},
        *[
            {"role": item["role"], "content": item["text"]}
            for item in fixture["source_messages"]
        ],
        {"role": fixture["request"]["role"], "content": fixture["request"]["text"]},
    ]
    envelope = replay.build_work_envelope(initial["text"], target, [])
    issued = replay.build_issued_messages(history, envelope, evidence)
    manifest.update(
        selected_source_ids=list(selected_ids),
        evidence_message=evidence,
        issued_messages=issued,
    )
    native._write_json(output / "manifest.json", manifest)
    try:
        worker_result = _perform_call(
            worker_client, issued, records[1], output, deadline, clock, manifest
        )
    except native.TechnicalError as exc:
        return _incomplete(manifest, output, exc, clock)

    try:
        applied = cpu.consume_action(
            initial["text"],
            initial["path"],
            target["symbol"],
            worker_result["arguments"],
        )
    except (KeyError, TypeError, cpu.PatchError) as exc:
        if clock() >= deadline:
            return _incomplete(
                manifest,
                output,
                native.TechnicalError(
                    "deadline", "worker action rejection was recorded late"
                ),
                clock,
            )
        records[1]["consumer"] = {
            "status": "REJECTED",
            "error": f"{type(exc).__name__}: {exc}",
        }
        _save_call(output, records[1])
        manifest.update(
            status="COMPLETE_NO_GO",
            technical_eligible=False,
            behavior_passed=False,
            ended_monotonic=clock(),
            consumer_failure={"kind": "action_rejected", "message": str(exc)},
            permanent_history=history
            + [envelope, copy.deepcopy(worker_result.get("assistant_message"))],
        )
        native._write_json(output / "manifest.json", manifest)
        return manifest

    if clock() >= deadline:
        return _incomplete(
            manifest,
            output,
            native.TechnicalError(
                "deadline", "worker action processing exceeded the deadline"
            ),
            clock,
        )
    native._write_text(output / "workspaces" / "after.py", applied.module)
    checks = cpu.cpu.run_checks(applied.module, _adapt_checks(fixture["checks"]))
    behavior_passed = bool(checks) and all(item["passed"] for item in checks)
    tool_message = _tool_feedback(worker_result["call_id"], applied)
    permanent = replay.commit_permanent_history(
        history, envelope, worker_result["assistant_message"], tool_message
    )
    if clock() >= deadline:
        return _incomplete(
            manifest,
            output,
            native.TechnicalError("deadline", "qualification publication was late"),
            clock,
        )
    records[1]["consumer"] = {
        "status": "APPLIED",
        "source_sha256": applied.source_sha256,
        "module_sha256": applied.module_sha256,
    }
    _save_call(output, records[1])
    if clock() >= deadline:
        return _incomplete(
            manifest,
            output,
            native.TechnicalError(
                "deadline", "qualification call receipt publication was late"
            ),
            clock,
        )
    manifest.update(
        status="COMPLETE",
        technical_eligible=True,
        behavior_passed=behavior_passed,
        ended_monotonic=clock(),
        permanent_history=permanent,
        check_results=checks,
    )
    native._write_json(output / "manifest.json", manifest)
    if clock() >= deadline:
        return _incomplete(
            manifest,
            output,
            native.TechnicalError(
                "deadline", "qualification final manifest publication was late"
            ),
            clock,
        )
    return manifest


def _local_token_counter(text):
    return len(cpu.cpu.slab.qwen_encode(text))


def _local_tokenizer_identity():
    path = cpu.cpu.slab.TOKENIZER_PATH.resolve()
    manifest = cpu.cpu.slab.tokenizer_manifest()
    return {"name": manifest["name"], "path": str(path), "sha256": manifest["sha256"]}


def _parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--base-url")
    parser.add_argument("--model")
    parser.add_argument("--deadline-seconds", type=float)
    parser.add_argument("--preflight-output", type=Path)
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    if args.preflight_output is not None:
        expected = args.input.with_name(PREFLIGHT_FILENAME).resolve()
        if args.preflight_output.resolve() != expected:
            raise ValueError(f"preflight output must be {expected}")
        if any(
            value is not None
            for value in (
                args.output_dir,
                args.base_url,
                args.model,
                args.deadline_seconds,
            )
        ):
            raise ValueError("preflight mode accepts only input and preflight-output")
        receipt = preflight_fixture(
            args.input, _local_token_counter, _local_tokenizer_identity()
        )
        native._write_json(args.preflight_output, receipt, exclusive=True)
        print(json.dumps(receipt, ensure_ascii=True, sort_keys=True))
        return 0 if receipt["status"] == "PASS" else 1
    if any(
        value is None
        for value in (args.output_dir, args.base_url, args.model, args.deadline_seconds)
    ):
        raise ValueError(
            "native mode requires output-dir, base-url, model and deadline-seconds"
        )
    fixture, _receipt = _read_fixture(args.input)
    eligible = [item["message_id"] for item in fixture["source_messages"]]
    selector = NativeSourceSelectorClient(args.base_url, args.model, eligible)
    worker = native.NativeToolClient(args.base_url, args.model)
    result = run_qualification(
        args.input,
        args.output_dir,
        selector,
        worker,
        deadline_seconds=args.deadline_seconds,
    )
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    if result["status"] == "COMPLETE" and result["technical_eligible"] is True:
        return 0
    if result["status"] == "COMPLETE_NO_GO":
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
