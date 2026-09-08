"""Four-call DEV diagnostic separating rule extraction from bookkeeping.

Only the two audited round-zero messages are model inputs.  Every case is
cold, gets one bounded HTTP attempt, and owns an independent empty register.
Transaction outputs are replayed through the unchanged updater without making
another network call.  No semantic answer key or automatic semantic score is
used here.
"""

import argparse
import base64
import hashlib
import json
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

try:
    from scripts import maintenance_dev_check as bounded
except ModuleNotFoundError:  # Direct ``python scripts/...`` invocation.
    import maintenance_dev_check as bounded

from stencil.focus import maintenance_bank, maintenance_updater
from stencil.focus.loop import Message
from stencil.focus.register import Register

EXPECTED_EPISODE_IDS = ("kimi-k3-dev-etl-01", "kimi-k3-dev-tscli-02")
EXPECTED_EPISODES = 2
EXPECTED_ROUNDS = 8
REQUEST_KIND = "code_answer"
SCHEDULE = (
    ("etl-prose", EXPECTED_EPISODE_IDS[0], "prose"),
    ("etl-transaction", EXPECTED_EPISODE_IDS[0], "transaction"),
    ("typescript-prose", EXPECTED_EPISODE_IDS[1], "prose"),
    ("typescript-transaction", EXPECTED_EPISODE_IDS[1], "transaction"),
)
SEMANTIC_INSTRUCTION = (
    "Identify every durable user rule in the source that is meant to govern "
    "future work. Include each rule's scope and modality (required, prohibited, "
    "permitted, or optional). Exclude background, project descriptions, one-off "
    "requests, and quoted material."
)


@dataclass(frozen=True)
class Case:
    call_index: int
    case_id: str
    episode_id: str
    domain: str
    representation: str
    task_handles: tuple[str, ...]
    source: Message
    register: Register
    issued_prompt: str
    validation_prompt: str | None
    base_state_sha256: str | None


class _ReplayDecoder:
    """Return one recorded response and expose the non-network validation prompt."""

    def __init__(self, raw_output):
        self.raw_output = raw_output
        self.calls = 0
        self.prompt = None

    def __call__(self, prompt):
        self.calls += 1
        self.prompt = prompt
        if self.calls != 1:
            raise RuntimeError("recorded response replayed more than once")
        if not isinstance(self.raw_output, str):
            raise bounded.DecodeFailure("network call produced no recorded raw output")
        return self.raw_output


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _request_body(prompt, model, max_tokens):
    payload = {
        "model": str(model),
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0,
        "seed": bounded.SEED,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    body = _canonical(payload).encode("utf-8")
    return payload, body


def _endpoint(base_url):
    value = str(base_url).rstrip("/")
    if not value.startswith(("http://", "https://")):
        value = "http://" + value
    return value + "/v1/chat/completions"


def _request_preview(prompt, base_url, model, max_tokens):
    payload, body = _request_body(prompt, model, max_tokens)
    return {
        "url": _endpoint(base_url),
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": body.decode("utf-8"),
        "body_base64": base64.b64encode(body).decode("ascii"),
        "body_sha256": hashlib.sha256(body).hexdigest(),
        "body_bytes": len(body),
        "json": payload,
    }


def _augment_request_bytes(http):
    if not isinstance(http, dict) or not isinstance(http.get("request"), dict):
        return
    request = http["request"]
    body = request.get("body")
    if not isinstance(body, str):
        return
    raw = body.encode("utf-8")
    request.update(
        body_base64=base64.b64encode(raw).decode("ascii"),
        body_sha256=hashlib.sha256(raw).hexdigest(),
        body_bytes=len(raw),
    )


def _load_cold_episodes(input_path):
    allocation = maintenance_bank.load_authored_bank(
        input_path,
        expected_episodes=EXPECTED_EPISODES,
        expected_rounds=EXPECTED_ROUNDS,
    )
    if allocation.split != "dev":
        raise ValueError("cold diagnostic refuses non-DEV input")
    if tuple(ep.episode_id for ep in allocation.episodes) != EXPECTED_EPISODE_IDS:
        raise ValueError("cold diagnostic requires the two audited Kimi episodes")
    episodes = {}
    for episode in allocation.episodes:
        if episode.task.request_kinds != (REQUEST_KIND,):
            raise ValueError("cold diagnostic requires the code_answer request kind")
        first = episode.rounds[0]
        if first.index != 0 or len(first.messages) != 1:
            raise ValueError("each cold source must be the sole round-zero message")
        authored = first.messages[0]
        source = Message(
            message_id=authored.message_id,
            role=authored.role,
            text=authored.content,
        )
        if source.role != "user" or source.origin != "direct":
            raise ValueError("each cold source must be a direct user message")
        episodes[episode.episode_id] = (episode, source)
    return allocation, episodes


def _common_prefix(source, task_handles):
    handles = ", ".join(task_handles)
    return (
        f"{SEMANTIC_INSTRUCTION}\n\n"
        f"Task handles: {handles}\n"
        f"Request kind: {REQUEST_KIND}\n\n"
        "--- SOURCE MESSAGE START ---\n"
        f"{source.text}\n"
        "--- SOURCE MESSAGE END ---"
    )


def _transaction_contract(validation_prompt):
    document = json.loads(validation_prompt)
    updater_input = document["input"]
    return {
        "instructions": document["instructions"],
        "lifecycle_rules": document["lifecycle_rules"],
        "caps": document["caps"],
        "supported_request_kinds": document["supported_request_kinds"],
        "response_schema": document["response_schema"],
        "input": {
            "base_state_sha256": updater_input["base_state_sha256"],
            "task_handles": updater_input["task_handles"],
            "request_kind": updater_input["request_kind"],
            "state": updater_input["state"],
        },
    }


def build_cases(input_path):
    """Build the exact fixed schedule without touching an output directory."""
    _allocation, episodes = _load_cold_episodes(Path(input_path))
    cases = []
    for call_index, (case_id, episode_id, representation) in enumerate(SCHEDULE):
        episode, source = episodes[episode_id]
        register = Register(task_handles=frozenset(episode.task.task_handles))
        prefix = _common_prefix(source, episode.task.task_handles)
        validation = None
        base_hash = None
        if representation == "prose":
            issued = (
                prefix + "\n\nReturn only a concise prose list. Do not return JSON."
            )
        else:
            prepared = maintenance_updater.build_prompt(
                register,
                source,
                task_handles=episode.task.task_handles,
                request_kind=REQUEST_KIND,
            )
            validation = prepared.text
            base_hash = prepared.base_state_sha256
            contract = _canonical(_transaction_contract(validation))
            issued = (
                prefix
                + "\n\nReturn only the JSON transaction required by the unchanged "
                "contract below.\n\n--- TRANSACTION CONTRACT START ---\n"
                + contract
                + "\n--- TRANSACTION CONTRACT END ---"
            )
        cases.append(
            Case(
                call_index,
                case_id,
                episode_id,
                episode.task.domain,
                representation,
                episode.task.task_handles,
                source,
                register,
                issued,
                validation,
                base_hash,
            )
        )
    return tuple(cases)


def preview(input_path, base_url, model, max_tokens):
    if type(max_tokens) is not int or max_tokens <= 0:
        raise ValueError("max_tokens must be a positive integer")
    requests = []
    for case in build_cases(input_path):
        requests.append(
            {
                "call_index": case.call_index,
                "case_id": case.case_id,
                "episode_id": case.episode_id,
                "representation": case.representation,
                "task_handles": list(case.task_handles),
                "request_kind": REQUEST_KIND,
                "source": {
                    "message_id": case.source.message_id,
                    "role": case.source.role,
                    "text": case.source.text,
                },
                "issued_prompt": case.issued_prompt,
                "issued_prompt_sha256": hashlib.sha256(
                    case.issued_prompt.encode("utf-8")
                ).hexdigest(),
                "http_request": _request_preview(
                    case.issued_prompt, base_url, model, max_tokens
                ),
                "validation_prompt": case.validation_prompt,
                "validation_prompt_sha256": (
                    hashlib.sha256(case.validation_prompt.encode("utf-8")).hexdigest()
                    if case.validation_prompt is not None
                    else None
                ),
            }
        )
    return {
        "schema_version": 1,
        "preview": True,
        "scheduled_cases": len(SCHEDULE),
        "network_calls": 0,
        "output_directory_mutated": False,
        "automatic_semantic_scoring": "none",
        "requests": requests,
    }


def _code_hashes():
    root = Path(__file__).resolve().parents[1]
    paths = {
        Path(__file__).resolve(),
        Path(bounded.__file__).resolve(),
        Path(maintenance_updater.__file__).resolve(),
        Path(maintenance_bank.__file__).resolve(),
        root / "src/stencil/focus/loop.py",
        root / "src/stencil/focus/register.py",
    }
    return {
        str(path.relative_to(root)): bounded.sha256_file(path)
        for path in sorted(paths, key=str)
    }


def _transaction_validation(case, raw_output):
    replay = _ReplayDecoder(raw_output)
    result = maintenance_updater.execute(
        register=case.register,
        source=case.source,
        decoder=replay,
        task_handles=case.task_handles,
        request_kind=REQUEST_KIND,
    )
    driver_errors = []
    if replay.calls != 1:
        driver_errors.append(f"expected one offline replay, observed {replay.calls}")
    if (
        result.prompt != case.validation_prompt
        or replay.prompt != case.validation_prompt
    ):
        driver_errors.append("validation prompt changed after case construction")
    if result.pre_state_sha256 != case.base_state_sha256:
        driver_errors.append("validation pre-state hash changed")
    if result.error is not None and result.register != case.register:
        driver_errors.append("rejected transaction changed its independent state")
    return result, driver_errors


def run(
    input_path,
    output_dir,
    decoder,
    *,
    deadline_seconds=300.0,
    runtime_args=None,
    clock=time.monotonic,
    wall_clock=time.time,
):
    """Attempt the four fixed cases once each and durably record every attempt."""
    if not callable(decoder):
        raise TypeError("decoder must be callable")
    if not isinstance(deadline_seconds, (int, float)) or deadline_seconds <= 0:
        raise ValueError("deadline_seconds must be positive")
    input_path = Path(input_path)
    cases = build_cases(input_path)
    root = bounded._prepare_output(output_dir)
    started_at = wall_clock()
    started = clock()
    deadline = started + float(deadline_seconds)
    if hasattr(decoder, "set_deadline"):
        decoder.set_deadline(deadline)
    audited = bounded._AuditedDecoder(
        decoder, root / "calls", clock=clock, wall_clock=wall_clock
    )
    manifest = {
        "schema_version": 1,
        "status": "INCOMPLETE",
        "reason": "run not completed",
        "started_at_unix": started_at,
        "finished_at_unix": None,
        "elapsed_seconds": None,
        "development_only": True,
        "data_lineage": {
            "fit_on": "none",
            "development_on": (
                "same two original Kimi-authored conversations and exposed "
                "DEV01/02 maintenance attempts"
            ),
            "evaluated_on": "none",
        },
        "audited_input": {
            "path": str(input_path),
            "sha256": bounded.sha256_file(input_path),
        },
        "code_sha256": _code_hashes(),
        "runtime_args": list(runtime_args) if runtime_args is not None else None,
        "runtime_config": {
            "deadline_seconds": float(deadline_seconds),
            "request_kind": REQUEST_KIND,
            "request_timeout_ceiling_seconds": bounded.REQUEST_TIMEOUT_SECONDS,
            "receipt_reserve_seconds": bounded.RECEIPT_RESERVE_SECONDS,
            "workers": 0,
            "retries": 0,
        },
        "automatic_semantic_scoring": "none",
        "scheduled_cases": len(cases),
        "case_order": [case.case_id for case in cases],
        "recorded_cases": 0,
        "decoder_calls": 0,
        "network_attempts": 0,
        "transport_errors": 0,
        "rows_path": "rows.jsonl",
        "calls_path": "calls",
    }
    bounded._write_json(root / "manifest.json", manifest)

    deadline_hit = False
    with (root / "rows.jsonl").open("x", encoding="utf-8") as rows_file:
        for case in cases:
            if clock() >= deadline - bounded.RECEIPT_RESERVE_SECONDS:
                deadline_hit = True
                break
            audited.set_context(case.call_index, case.episode_id, 0)
            before_receipts = len(audited.receipts)
            decoded_output = None
            transport_error = None
            try:
                decoded_output = audited(case.issued_prompt)
            except Exception as exc:
                transport_error = bounded._exception_text(exc)

            receipt_path = None
            receipt = None
            driver_errors = []
            receipt_delta = len(audited.receipts) - before_receipts
            if receipt_delta != 1:
                driver_errors.append(
                    f"expected one decoder receipt, observed {receipt_delta}"
                )
            else:
                receipt_path, receipt = audited.receipts[-1]
                _augment_request_bytes(receipt.get("http"))
                bounded._write_json(receipt_path, receipt)
            raw_output = (
                receipt.get("raw_output") if receipt is not None else decoded_output
            )
            http = receipt.get("http") if receipt is not None else None
            network_attempted = isinstance(http, dict) and isinstance(
                http.get("request"), dict
            )

            if case.representation == "transaction":
                replay_output = raw_output if transport_error is None else None
                result, validation_errors = _transaction_validation(case, replay_output)
                driver_errors.extend(validation_errors)
                structural_validation = {
                    "applicable": True,
                    "status": "ACCEPTED" if result.accepted else "REJECTED",
                    "accepted": result.accepted,
                    "error": result.error,
                    "accepted_ops": [asdict(entry) for entry in result.accepted_ops],
                    "pre_state": bounded._state_snapshot(case.register),
                    "post_state": bounded._state_snapshot(result.register),
                    "pre_state_sha256": result.pre_state_sha256,
                    "post_state_sha256": result.post_state_sha256,
                }
            else:
                structural_validation = {
                    "applicable": False,
                    "status": "N/A",
                    "accepted": None,
                    "error": None,
                    "accepted_ops": "N/A",
                    "pre_state": "N/A",
                    "post_state": "N/A",
                    "pre_state_sha256": "N/A",
                    "post_state_sha256": "N/A",
                }

            row = {
                "schema_version": 1,
                "call_index": case.call_index,
                "case_id": case.case_id,
                "episode_id": case.episode_id,
                "domain": case.domain,
                "representation": case.representation,
                "source": {
                    "message_id": case.source.message_id,
                    "role": case.source.role,
                    "text": case.source.text,
                },
                "task_handles": list(case.task_handles),
                "request_kind": REQUEST_KIND,
                "issued_prompt": case.issued_prompt,
                "issued_prompt_sha256": hashlib.sha256(
                    case.issued_prompt.encode("utf-8")
                ).hexdigest(),
                "validation_prompt": case.validation_prompt,
                "validation_prompt_sha256": (
                    hashlib.sha256(case.validation_prompt.encode("utf-8")).hexdigest()
                    if case.validation_prompt is not None
                    else None
                ),
                "raw_output": raw_output,
                "transport_error": transport_error,
                "driver_errors": driver_errors,
                "network_attempted": network_attempted,
                "token_usage": (http.get("usage") if isinstance(http, dict) else None),
                "started_at_unix": (
                    receipt.get("started_at_unix") if receipt is not None else None
                ),
                "elapsed_seconds": (
                    receipt.get("elapsed_seconds") if receipt is not None else None
                ),
                "call_receipt": (
                    str(receipt_path.relative_to(root))
                    if receipt_path is not None
                    else None
                ),
                "structural_validation": structural_validation,
                "automatic_semantic_score": None,
            }
            bounded._append_jsonl(rows_file, row)
            manifest["recorded_cases"] += 1
            manifest["decoder_calls"] = len(audited.receipts)
            manifest["network_attempts"] += int(network_attempted)
            manifest["transport_errors"] += int(transport_error is not None)
            bounded._write_json(root / "manifest.json", manifest)

    elapsed = clock() - started
    complete = (
        not deadline_hit
        and manifest["recorded_cases"] == len(cases)
        and manifest["decoder_calls"] == len(cases)
        and manifest["network_attempts"] == len(cases)
        and elapsed <= deadline_seconds
    )
    if complete:
        reason = None
    elif deadline_hit:
        reason = "deadline before next scheduled case"
    elif elapsed > deadline_seconds:
        reason = "deadline exceeded after a scheduled attempt"
    else:
        reason = "scheduled attempt or receipt accounting incomplete"
    manifest.update(
        status="COMPLETE" if complete else "INCOMPLETE",
        reason=reason,
        finished_at_unix=wall_clock(),
        elapsed_seconds=elapsed,
    )
    bounded._write_json(root / "manifest.json", manifest)
    return manifest


def _parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:18088")
    parser.add_argument("--model", default="/model")
    parser.add_argument("--max-tokens", type=int, default=1024)
    parser.add_argument("--deadline-seconds", type=float, default=300.0)
    parser.add_argument("--preview", action="store_true")
    return parser


def main(argv=None):
    runtime_args = list(sys.argv[1:] if argv is None else argv)
    args = _parser().parse_args(runtime_args)
    if args.preview:
        planned = preview(args.input, args.base_url, args.model, args.max_tokens)
        print(json.dumps(planned, ensure_ascii=False, sort_keys=True), flush=True)
        return 0
    decoder = bounded.ChatCompletionDecoder(args.base_url, args.model, args.max_tokens)
    manifest = run(
        args.input,
        args.output_dir,
        decoder,
        deadline_seconds=args.deadline_seconds,
        runtime_args=runtime_args,
    )
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True), flush=True)
    return 0 if manifest["status"] == "COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
