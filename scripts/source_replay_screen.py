#!/usr/bin/env python3
"""Preflight or run the fixed four-project H/S/R source-replay screen."""

import argparse
import base64
import copy
import hashlib
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
from scripts import source_replay_qualification as qualified  # noqa: E402
from stencil import source_replay as replay  # noqa: E402
from stencil import source_replay_screen as contract  # noqa: E402
from stencil.focus.native_source_selector import (  # noqa: E402
    NativeSourceSelectorClient,
)

SCHEMA_VERSION = 1
PREFLIGHT_FILENAME = "screen-preflight.json"
DEFAULT_DEADLINE_SECONDS = 2340.0
PAIR_DEADLINE_SECONDS = 181.0
PREFLIGHT_CODE_FILES = (
    "scripts/source_replay_screen.py",
    "src/stencil/source_replay_screen.py",
    "src/stencil/source_replay.py",
    "src/stencil/focus/native_source_selector.py",
    "scripts/source_replay_qualification.py",
    "scripts/coding_competence_run.py",
    "scripts/coding_competence_dev.py",
    "scripts/coding_worker_dev.py",
    "src/stencil/focus/slab.py",
    "src/stencil/focus/slab_sandbox.py",
    "src/stencil/focus/renderer.py",
)


def _sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def _reject_duplicate_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _read_json(path, label):
    try:
        body = Path(path).read_bytes()
        value = json.loads(body, object_pairs_hook=_reject_duplicate_object)
    except Exception as exc:
        raise ValueError(f"{label} is not readable strict JSON: {exc}") from exc
    return value, body


def _resolve(root, relative, label):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError(f"{label} must be a repository-relative path")
    root = Path(root).resolve()
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{label} escapes the repository") from exc
    return path


def _read_binding(root, binding, label):
    path = _resolve(root, binding["path"], label)
    if not path.is_file():
        raise ValueError(f"{label} is missing")
    body = path.read_bytes()
    if _sha_bytes(body) != binding["sha256"]:
        raise ValueError(f"{label} hash mismatch")
    return path, body


def _input_receipt(path, body):
    return {
        "path": str(Path(path).resolve()),
        "bytes": len(body),
        "sha256": _sha_bytes(body),
    }


def _code_hashes():
    return {
        relative: _sha_bytes((ROOT / relative).read_bytes())
        for relative in PREFLIGHT_CODE_FILES
    }


def _adapt_checks(checks):
    return [
        {key: copy.deepcopy(item[key]) for key in contract.EXECUTABLE_CHECK_FIELDS}
        | {"rule_ids": []}
        for item in checks
    ]


def load_inputs(input_path, *, root=ROOT):
    """Load and hash the exact root manifest, four projects, and evidence files."""
    value, body = _read_json(input_path, "screen input")
    manifest = contract.validate_input_manifest(value)
    projects = []
    project_receipts = []
    for index, binding in enumerate(manifest["projects"]):
        path, project_body = _read_binding(root, binding, f"project {index + 1}")
        project_value, parsed_body = _read_json(path, f"project {index + 1}")
        if parsed_body != project_body:
            raise AssertionError("project bytes changed during one read")
        projects.append(contract.validate_project(project_value))
        project_receipts.append(
            {
                "path": binding["path"],
                "bytes": len(project_body),
                "sha256": binding["sha256"],
            }
        )
    project_ids = [item["public"]["project_id"] for item in projects]
    if len(set(project_ids)) != contract.PROJECTS:
        raise ValueError("project IDs must be unique across the screen")
    evidence = {"source_review": manifest["source_review"], **manifest["qualification"]}
    evidence_receipts = {}
    evidence_values = {}
    for role, binding in evidence.items():
        path, evidence_body = _read_binding(root, binding, role)
        evidence_receipts[role] = {
            "path": binding["path"],
            "bytes": len(evidence_body),
            "sha256": binding["sha256"],
        }
        if role not in {"source_review", "result_review"}:
            evidence_values[role], _ = _read_json(path, role)
    return {
        "manifest": manifest,
        "input_receipt": _input_receipt(input_path, body),
        "projects": projects,
        "project_receipts": project_receipts,
        "evidence_receipts": evidence_receipts,
        "evidence_values": evidence_values,
    }


def _qualification_render_bound(values):
    manifest = values.get("manifest")
    lifecycle = values.get("lifecycle")
    terminal = values.get("terminal")
    if (
        type(manifest) is not dict
        or manifest.get("status") != "COMPLETE"
        or manifest.get("technical_eligible") is not True
        or type(manifest.get("model_calls")) is not int
        or manifest.get("model_calls") != 2
        or type(lifecycle) is not dict
        or lifecycle.get("cleaned") is not True
        or lifecycle.get("status") != "DRIVER_EXITED"
        or type(lifecycle.get("elapsed_seconds")) not in {int, float}
        or isinstance(lifecycle.get("elapsed_seconds"), bool)
        or not math.isfinite(lifecycle["elapsed_seconds"])
        or lifecycle["elapsed_seconds"] < 0
        or lifecycle["elapsed_seconds"] > 600
        or type(terminal) is not dict
        or terminal.get("status") != "ELIGIBLE"
        or terminal.get("technical_eligible") is not True
    ):
        raise ValueError("qualification evidence is not a completed eligible lifecycle")
    elapsed = []
    for expected_index, role in enumerate(("selector_call", "worker_call")):
        record = values.get(role)
        exchange = record.get("exchange") if type(record) is dict else None
        render = exchange.get("render") if type(exchange) is dict else None
        value = render.get("elapsed_seconds") if type(render) is dict else None
        if (
            type(record) is not dict
            or type(record.get("index")) is not int
            or record.get("index") != expected_index
            or record.get("status") != "COMPLETE"
            or type(exchange) is not dict
            or exchange.get("status") != "COMPLETE"
            or isinstance(value, bool)
            or type(value) not in {int, float}
            or not math.isfinite(value)
            or value < 0
        ):
            raise ValueError(f"qualification {role} is not a complete native call")
        elapsed.append(value)
    return max(elapsed)


def _tokenizer(tokenizer_identity):
    if type(tokenizer_identity) is not dict or set(tokenizer_identity) != {
        "name",
        "path",
        "sha256",
    }:
        raise ValueError("tokenizer_identity has the wrong fields")
    path = Path(tokenizer_identity["path"])
    if (
        not isinstance(tokenizer_identity["name"], str)
        or not tokenizer_identity["name"]
        or not path.is_file()
        or _sha_bytes(path.read_bytes()) != tokenizer_identity["sha256"]
    ):
        raise ValueError("tokenizer_identity does not bind an existing tokenizer")
    return copy.deepcopy(tokenizer_identity)


def _argument_receipt(source, token_counter):
    body = native._json_bytes({"source": source})
    tokens = token_counter(body.decode("utf-8"))
    if type(tokens) is not int or tokens < 0:
        raise ValueError("token_counter must return a nonnegative integer")
    response_tokens = tokens + 1
    return {
        "body": body.decode("utf-8"),
        "body_base64": base64.b64encode(body).decode("ascii"),
        "body_bytes": len(body),
        "body_sha256": _sha_bytes(body),
        "argument_tokens": tokens,
        "eos_allowance_tokens": 1,
        "response_tokens_with_eos": response_tokens,
        "generation_headroom": contract.WORKER_CAP - response_tokens,
    }


def preflight_inputs(input_path, token_counter, tokenizer_identity, *, root=ROOT):
    """Apply all references and mutants once through the actual CPU consumers."""
    loaded = load_inputs(input_path, root=root)
    tokenizer = _tokenizer(tokenizer_identity)
    r = _qualification_render_bound(loaded["evidence_values"])
    project_records = []
    all_elapsed = []
    active_count_sum = 0
    eligible = True
    for document, project_receipt in zip(
        loaded["projects"], loaded["project_receipts"], strict=True
    ):
        public = document["public"]
        module = public["initial_file"]["text"]
        references = []
        final_designated_reference = None
        for round_index in range(1, contract.ROUNDS + 1):
            before = module
            target = public["rounds"][round_index - 1]["target"]
            source = document["private"]["rounds"][round_index - 1]["reference_patch"]
            try:
                action = cpu.consume_action(
                    module, target["path"], target["symbol"], {"source": source}
                )
            except cpu.PatchError as exc:
                raise ValueError(f"reference is not consumable: {exc}") from exc
            module = action.module
            public_checks, private_checks = contract.active_checks(
                document, round_index
            )
            active_count_sum += len(public_checks) + len(private_checks)
            public_results = cpu.cpu.run_checks(module, _adapt_checks(public_checks))
            private_results = cpu.cpu.run_checks(module, _adapt_checks(private_checks))
            all_results = [*public_results, *private_results]
            all_elapsed.extend(item["elapsed_seconds"] for item in all_results)
            argument = _argument_receipt(source, token_counter)
            passed = bool(all_results) and all(item["passed"] for item in all_results)
            reference = {
                "round_index": round_index,
                "target": copy.deepcopy(target),
                "module_before": before,
                "module_before_sha256": native._sha_text(before),
                "module_after": module,
                "module_after_sha256": action.module_sha256,
                "source_sha256": action.source_sha256,
                "argument": argument,
                "generation_headroom": argument["generation_headroom"],
                "public_results": public_results,
                "private_results": private_results,
                "all_checks_passed": passed,
            }
            references.append(reference)
            eligible = (
                eligible
                and passed
                and argument["generation_headroom"] >= contract.MIN_REFERENCE_HEADROOM
            )
            failing_id = document["private"]["obsolete_mutant"]["failing_check_id"]
            if round_index == 3:
                final_designated_reference = next(
                    (
                        item
                        for item in private_results
                        if item["check_id"] == failing_id
                    ),
                    None,
                )
        mutant_source = document["private"]["obsolete_mutant"]["source"]
        final_target = public["rounds"][-1]["target"]
        try:
            mutant_action = cpu.consume_action(
                module,
                final_target["path"],
                final_target["symbol"],
                {"source": mutant_source},
            )
        except cpu.PatchError as exc:
            raise ValueError(f"obsolete mutant is not consumable: {exc}") from exc
        failing_id = document["private"]["obsolete_mutant"]["failing_check_id"]
        designated_check = next(
            item
            for item in contract.active_checks(document, 3)[1]
            if item["check_id"] == failing_id
        )
        mutant_results = cpu.cpu.run_checks(
            mutant_action.module, _adapt_checks([designated_check])
        )
        all_elapsed.extend(item["elapsed_seconds"] for item in mutant_results)
        mutant_passes_vacuously = (
            final_designated_reference is None
            or final_designated_reference["passed"] is not True
            or len(mutant_results) != 1
            or mutant_results[0]["passed"] is True
        )
        eligible = eligible and not mutant_passes_vacuously
        project_records.append(
            {
                "project_id": public["project_id"],
                "input": project_receipt,
                "references": references,
                "mutant": {
                    "source_sha256": mutant_action.source_sha256,
                    "module_sha256": mutant_action.module_sha256,
                    "failing_check_id": failing_id,
                    "reference_designated_result": final_designated_reference,
                    "designated_result": mutant_results[0],
                    "vacuity_rejected": not mutant_passes_vacuously,
                },
            }
        )
    q = max(all_elapsed, default=0.0)
    c = 3 * active_count_sum
    projection = contract.projected_seconds(c, q, r)
    eligible = eligible and projection <= 3000
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": "source-replay-screen-cpu-preflight",
        "status": "PASS" if eligible else "INELIGIBLE",
        "model_calls": 0,
        "input": loaded["input_receipt"],
        "consumer_code_sha256": _code_hashes(),
        "tokenizer": tokenizer,
        "projects": project_records,
        "project_inputs": loaded["project_receipts"],
        "evidence": loaded["evidence_receipts"],
        "projection": {
            "C": c,
            "q": q,
            "r": r,
            "historical_generation_seconds": contract.HISTORICAL_GENERATION_SECONDS,
            "projected_seconds": projection,
            "reservation_seconds": 3000,
            "eligible": projection <= 3000,
        },
    }


def _validate_preflight(path, loaded):
    value, _ = _read_json(path, "screen CPU preflight")
    if (
        type(value) is not dict
        or type(value.get("schema_version")) is not int
        or value.get("schema_version") != 1
        or value.get("kind") != "source-replay-screen-cpu-preflight"
        or value.get("status") != "PASS"
        or type(value.get("model_calls")) is not int
        or value.get("model_calls") != 0
        or value.get("input") != loaded["input_receipt"]
        or value.get("consumer_code_sha256") != _code_hashes()
        or value.get("project_inputs") != loaded["project_receipts"]
        or value.get("evidence") != loaded["evidence_receipts"]
    ):
        raise ValueError("screen CPU preflight is stale or ineligible")
    _tokenizer(value.get("tokenizer"))
    projects = value.get("projects")
    if type(projects) is not list or len(projects) != 4:
        raise ValueError("screen CPU preflight lacks four project records")
    for item in projects:
        references = item.get("references") if type(item) is dict else None
        mutant = item.get("mutant") if type(item) is dict else None
        if (
            type(references) is not list
            or len(references) != 3
            or any(
                reference.get("all_checks_passed") is not True
                or type(reference.get("generation_headroom")) is not int
                or reference["generation_headroom"] < contract.MIN_REFERENCE_HEADROOM
                for reference in references
            )
            or type(mutant) is not dict
            or mutant.get("vacuity_rejected") is not True
        ):
            raise ValueError("screen CPU preflight project record is ineligible")
    projection = value.get("projection")
    if (
        type(projection) is not dict
        or projection.get("eligible") is not True
        or projection.get("reservation_seconds") != 3000
        or type(projection.get("C")) is not int
        or projection["C"] <= 0
        or type(projection.get("q")) not in {int, float}
        or isinstance(projection.get("q"), bool)
        or type(projection.get("r")) not in {int, float}
        or isinstance(projection.get("r"), bool)
        or projection.get("projected_seconds")
        != contract.projected_seconds(projection["C"], projection["q"], projection["r"])
        or projection["projected_seconds"] > 3000
    ):
        raise ValueError("screen CPU preflight projection is invalid")
    return value


def _prepare_output(path, slots):
    output = Path(path)
    if output.exists():
        if not output.is_dir() or any(output.iterdir()):
            raise FileExistsError("refuse existing nonempty output directory")
    else:
        output.mkdir(parents=True)
    (output / "calls").mkdir()
    (output / "rounds").mkdir()
    for slot in slots:
        native._write_json(
            output / "calls" / f"call-{slot['slot_index']:04d}.json",
            slot,
            exclusive=True,
        )
    return output


def _http_elapsed(record):
    exchange = record.get("exchange") or {}
    return sum(
        value
        for value in (
            (exchange.get("render") or {}).get("elapsed_seconds"),
            (exchange.get("completion") or {}).get("elapsed_seconds"),
        )
        if type(value) in {int, float} and not isinstance(value, bool)
    )


def _feedback(call_id, applied, error, module, public_results):
    content = {
        "action_status": "applied" if applied else "rejected",
        "action_error": error,
        "current_module": {"path": "module.py", "text": module},
        "public_checks": copy.deepcopy(public_results),
    }
    return {
        "role": "tool",
        "tool_call_id": call_id,
        "name": "replace_function",
        "content": replay.canonical_json(content),
    }


def _save_manifest(output, manifest):
    native._write_json(output / "manifest.json", manifest)


def _record_call(client, messages, record, output, deadline, clock, manifest):
    result = qualified._perform_call(
        client, messages, record, output, deadline, clock, manifest
    )
    record["usage"] = copy.deepcopy(result["usage"])
    record["http_elapsed_seconds"] = _http_elapsed(record)
    native._write_json(output / "calls" / f"call-{record['index']:04d}.json", record)
    return result


def run_screen(
    input_path,
    output_dir,
    selector_factory=None,
    worker_client=None,
    *,
    base_url="http://127.0.0.1:18088",
    model="/model",
    deadline_seconds=DEFAULT_DEADLINE_SECONDS,
    clock=time.monotonic,
    runtime_args=None,
    root=ROOT,
):
    """Run the exact serial schedule; injectable clients are for CPU software tests."""
    if (
        isinstance(deadline_seconds, bool)
        or type(deadline_seconds) not in {int, float}
        or not math.isfinite(deadline_seconds)
        or deadline_seconds <= 0
    ):
        raise ValueError("deadline_seconds must be positive and finite")
    started = clock()
    deadline = started + deadline_seconds
    loaded = load_inputs(input_path, root=root)
    preflight = _validate_preflight(
        Path(input_path).with_name(PREFLIGHT_FILENAME), loaded
    )
    slots = contract.planned_slots(loaded["projects"])
    records = [dict(slot, index=slot["slot_index"]) for slot in slots]
    output = _prepare_output(output_dir, records)
    states = {}
    for document in loaded["projects"]:
        for arm in contract.ARMS:
            states[f"{document['public']['project_id']}:{arm}"] = {
                "module": document["public"]["initial_file"]["text"],
                "permanent_history": [
                    {"role": "system", "content": native.SYSTEM_PROMPT}
                ],
            }
    intervention = {
        "events": [],
        "schedule_automatic": True,
        "manual_action_interface": False,
        "retries": 0,
        "actual_requests_recorded": True,
        "runtime_args": list(runtime_args) if runtime_args is not None else None,
    }
    manifest = {
        "schema_version": 1,
        "kind": "source-replay-screen-native-run",
        "status": "IN_PROGRESS",
        "gate_disposition": None,
        "started_monotonic": started,
        "deadline_monotonic": deadline,
        "ended_monotonic": None,
        "input": loaded["input_receipt"],
        "preflight": preflight,
        "model_calls": 0,
        "calls": records,
        "rounds": [],
        "states": states,
        "intervention_evidence": intervention,
        "technical_failure": None,
        "outcomes": None,
    }
    _save_manifest(output, manifest)
    if selector_factory is None:

        def selector_factory(ids):
            return NativeSourceSelectorClient(base_url, model, ids)

    if worker_client is None:
        worker_client = native.NativeToolClient(base_url, model)

    slots_by_key = {
        (item["project_index"], item["round_index"], item["arm"], item["kind"]): item
        for item in records
    }
    try:
        for project_index, document in enumerate(loaded["projects"]):
            public = document["public"]
            project_id = public["project_id"]
            for round_zero, public_round in enumerate(public["rounds"]):
                round_index = round_zero + 1
                offset = (project_index + round_zero) % len(contract.ARMS)
                arms = contract.ARMS[offset:] + contract.ARMS[:offset]
                eligible = contract.eligible_originals(document, round_index)
                public_checks, private_checks = contract.active_checks(
                    document, round_index
                )
                public_projection = [
                    {
                        key: copy.deepcopy(item[key])
                        for key in contract.EXECUTABLE_CHECK_FIELDS
                    }
                    for item in public_checks
                ]
                for arm in arms:
                    state = states[f"{project_id}:{arm}"]
                    state["permanent_history"].extend(
                        {"role": item["role"], "content": item["text"]}
                        for item in [
                            *public_round["source_messages"],
                            public_round["request"],
                        ]
                    )
                    selected_ids = []
                    supplement = None
                    if arm == "S":
                        selector_record = slots_by_key[
                            (project_index, round_index, arm, "selector")
                        ]
                        selector_record["eligible_originals"] = copy.deepcopy(eligible)
                        selector_messages = replay.build_selector_messages(
                            eligible, public_round["request"]
                        )
                        selector_record["issued_messages"] = copy.deepcopy(
                            selector_messages
                        )
                        client = selector_factory(
                            [item["message_id"] for item in eligible]
                        )
                        selector_result = _record_call(
                            client,
                            selector_messages,
                            selector_record,
                            output,
                            deadline,
                            clock,
                            manifest,
                        )
                        try:
                            selected_ids = selector_result["arguments"]["source_ids"]
                            supplement = replay.render_evidence(eligible, selected_ids)
                        except (KeyError, TypeError, ValueError) as exc:
                            raise native.TechnicalError(
                                "source_consumer",
                                f"selector output was not consumable: {exc}",
                            ) from exc
                        selector_record["consumer"] = {
                            "status": "ACCEPTED",
                            "selected_source_ids": list(selected_ids),
                        }
                        native._write_json(
                            output
                            / "calls"
                            / f"call-{selector_record['index']:04d}.json",
                            selector_record,
                        )
                    elif arm == "R":
                        selected = contract.recency_originals(document, round_index)
                        selected_ids = [item["message_id"] for item in selected]
                        supplement = replay.render_evidence(eligible, selected_ids)

                    module_before = state["module"]
                    envelope = replay.build_work_envelope(
                        module_before, public_round["target"], public_projection
                    )
                    issued = replay.build_issued_messages(
                        state["permanent_history"], envelope, supplement
                    )
                    worker_record = slots_by_key[
                        (project_index, round_index, arm, "worker")
                    ]
                    worker_record.update(
                        selected_source_ids=list(selected_ids),
                        evidence_message=copy.deepcopy(supplement),
                        issued_messages=copy.deepcopy(issued),
                        module_before_sha256=native._sha_text(module_before),
                    )
                    result = _record_call(
                        worker_client,
                        issued,
                        worker_record,
                        output,
                        deadline,
                        clock,
                        manifest,
                    )
                    applied = False
                    action_error = None
                    try:
                        action = cpu.consume_action(
                            module_before,
                            public_round["target"]["path"],
                            public_round["target"]["symbol"],
                            result["arguments"],
                        )
                        state["module"] = action.module
                        applied = True
                    except cpu.PatchError as exc:
                        action_error = f"{type(exc).__name__}: {exc}"
                    public_results = cpu.cpu.run_checks(
                        state["module"], _adapt_checks(public_checks)
                    )
                    private_results = cpu.cpu.run_checks(
                        state["module"], _adapt_checks(private_checks)
                    )
                    successful = (
                        applied
                        and bool([*public_results, *private_results])
                        and all(
                            item["passed"]
                            for item in [*public_results, *private_results]
                        )
                    )
                    tool_message = _feedback(
                        result["call_id"],
                        applied,
                        action_error,
                        state["module"],
                        public_results,
                    )
                    state["permanent_history"] = replay.commit_permanent_history(
                        state["permanent_history"],
                        envelope,
                        result["assistant_message"],
                        tool_message,
                    )
                    worker_record["consumer"] = {
                        "status": "APPLIED" if applied else "REJECTED",
                        "error": action_error,
                        "module_after_sha256": native._sha_text(state["module"]),
                    }
                    native._write_json(
                        output / "calls" / f"call-{worker_record['index']:04d}.json",
                        worker_record,
                    )
                    round_record = {
                        "project_index": project_index,
                        "project_id": project_id,
                        "round_index": round_index,
                        "arm": arm,
                        "applied": applied,
                        "action_error": action_error,
                        "module_before": module_before,
                        "module_after": state["module"],
                        "selected_source_ids": list(selected_ids),
                        "issued_messages": issued,
                        "tool_message": tool_message,
                        "public_results": public_results,
                        "private_results": private_results,
                        "successful": successful,
                    }
                    manifest["rounds"].append(round_record)
                    native._write_json(
                        output
                        / "rounds"
                        / f"round-{project_index}-{round_index}-{arm}.json",
                        round_record,
                        exclusive=True,
                    )
                    manifest["calls"] = records
                    manifest["states"] = states
                    _save_manifest(output, manifest)
                    if clock() >= deadline:
                        raise native.TechnicalError(
                            "deadline",
                            "screen receipt publication crossed the driver deadline",
                        )
    except native.TechnicalError as exc:
        manifest.update(
            status="INCOMPLETE",
            gate_disposition="INCOMPLETE",
            ended_monotonic=clock(),
            technical_failure={"kind": exc.kind, "message": str(exc)},
            calls=records,
            states=states,
        )
        _save_manifest(output, manifest)
        return manifest

    gate = contract.evaluate_gate(manifest["rounds"], records, intervention)
    behavior_failures = {behavior: 0 for behavior in contract.BEHAVIORS}
    for round_record in manifest["rounds"]:
        metadata = {
            item["check_id"]: item["behavior"]
            for item in (
                *contract.active_checks(
                    loaded["projects"][round_record["project_index"]],
                    round_record["round_index"],
                ),
            )
            for item in item
        }
        for result in [
            *round_record["public_results"],
            *round_record["private_results"],
        ]:
            if not result["passed"]:
                behavior_failures[metadata[result["check_id"]]] += 1
    manifest.update(
        status="COMPLETE",
        gate_disposition=gate["disposition"],
        ended_monotonic=clock(),
        outcomes={**gate, "behavior_failures": behavior_failures},
        calls=records,
        states=states,
    )
    _save_manifest(output, manifest)
    if clock() >= deadline:
        exc = native.TechnicalError(
            "deadline", "screen final manifest publication was late"
        )
        manifest.update(
            status="INCOMPLETE",
            gate_disposition="INCOMPLETE",
            ended_monotonic=clock(),
            technical_failure={"kind": exc.kind, "message": str(exc)},
        )
        _save_manifest(output, manifest)
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
        receipt = preflight_inputs(
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
    result = run_screen(
        args.input,
        args.output_dir,
        base_url=args.base_url,
        model=args.model,
        deadline_seconds=args.deadline_seconds,
        runtime_args=sys.argv[1:] if argv is None else argv,
    )
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    if result["status"] != "COMPLETE":
        return 2
    return 0 if result["gate_disposition"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
