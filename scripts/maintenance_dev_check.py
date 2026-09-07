"""Sequential, DEV-only research driver for automatic register maintenance.

This module owns no server or process lifecycle.  The caller supplies an already
available decoder (the CLI constructs the HTTP decoder), and every scheduled
message gets at most one updater call.  Gold annotations are loaded only to
validate the authored DEV bank; they never enter updater arguments or prompts.
"""

import argparse
import base64
import hashlib
import json
import sys
import time
from dataclasses import asdict, replace
from http.client import IncompleteRead
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request as HTTPRequest
from urllib.request import urlopen

from stencil.focus import maintenance_bank, maintenance_updater
from stencil.focus.loop import Message
from stencil.focus.register import Register

EXPECTED_EPISODES = 2
EXPECTED_ROUNDS = 8
REQUEST_TIMEOUT_SECONDS = 60.0
RECEIPT_RESERVE_SECONDS = 1.0
SEED = 20260907


class DecodeFailure(RuntimeError):
    """A recorded response cannot safely be passed to the updater compiler."""


class DeadlineExceeded(DecodeFailure):
    """The request cannot finish while preserving time to write its receipt."""


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _exception_text(exc):
    return f"{type(exc).__name__}: {exc}"


def _json_bytes(value):
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()


def _write_json(path, value, *, exclusive=False):
    mode = "x" if exclusive else "w"
    with Path(path).open(mode, encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()


def _append_jsonl(handle, value):
    handle.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n")
    handle.flush()


def _response_headers(response):
    headers = getattr(response, "headers", None)
    if headers is None:
        return {}
    return dict(headers.items()) if hasattr(headers, "items") else dict(headers)


def _response_receipt(response, body, *, incomplete_expected_bytes=None):
    body = bytes(body)
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError:
        text = None
    receipt = {
        "status": getattr(response, "status", getattr(response, "code", None)),
        "headers": _response_headers(response),
        "body": text,
        "body_base64": base64.b64encode(body).decode("ascii"),
        "body_sha256": hashlib.sha256(body).hexdigest(),
        "body_bytes": len(body),
    }
    if incomplete_expected_bytes is not None:
        receipt["incomplete_read_expected_bytes"] = incomplete_expected_bytes
    return receipt


class ChatCompletionDecoder:
    """One-shot stdlib transport for an already-running chat-completions server."""

    def __init__(
        self,
        base_url,
        model,
        max_tokens,
        *,
        opener=None,
        clock=time.monotonic,
    ):
        if type(max_tokens) is not int or max_tokens <= 0:
            raise ValueError("max_tokens must be a positive integer")
        base_url = str(base_url).rstrip("/")
        if not base_url.startswith(("http://", "https://")):
            base_url = "http://" + base_url
        self.endpoint = base_url + "/v1/chat/completions"
        self.model = str(model)
        self.max_tokens = max_tokens
        self.opener = opener
        self.clock = clock
        self.deadline = None
        self.last_http = None

    def set_deadline(self, deadline):
        self.deadline = deadline

    def _timeout(self):
        if self.deadline is None:
            return REQUEST_TIMEOUT_SECONDS
        remaining = self.deadline - self.clock() - RECEIPT_RESERVE_SECONDS
        if remaining <= 0:
            raise DeadlineExceeded("deadline leaves no time for a durable receipt")
        return min(REQUEST_TIMEOUT_SECONDS, remaining)

    def __call__(self, prompt):
        if not isinstance(prompt, str):
            raise TypeError("decoder prompt must be a string")
        self.last_http = None
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.max_tokens,
            "temperature": 0,
            "seed": SEED,
            "chat_template_kwargs": {"enable_thinking": False},
        }
        timeout = self._timeout()
        request_body = _json_bytes(payload)
        request = HTTPRequest(
            self.endpoint,
            data=request_body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        exchange = {
            "request": {
                "url": self.endpoint,
                "method": "POST",
                "headers": {"Content-Type": "application/json"},
                "timeout_seconds": timeout,
                "body": request_body.decode("utf-8"),
                "json": payload,
            },
            "response": None,
            "finish_reason": None,
            "raw_output": None,
            "usage": None,
            "error": None,
        }
        self.last_http = exchange
        opener = self.opener or urlopen
        try:
            with opener(request, timeout=timeout) as response:
                try:
                    response_body = response.read()
                except IncompleteRead as exc:
                    exchange["response"] = _response_receipt(
                        response,
                        exc.partial,
                        incomplete_expected_bytes=exc.expected,
                    )
                    raise DecodeFailure(
                        f"HTTP response read failure: {_exception_text(exc)}"
                    ) from exc
                exchange["response"] = _response_receipt(response, response_body)
        except DecodeFailure as exc:
            exchange["error"] = _exception_text(exc)
            raise
        except HTTPError as exc:
            incomplete = None
            try:
                body = exc.read()
            except IncompleteRead as read_exc:
                body = read_exc.partial
                incomplete = read_exc.expected
            exchange["response"] = _response_receipt(
                exc, body, incomplete_expected_bytes=incomplete
            )
            exchange["error"] = _exception_text(exc)
            raise DecodeFailure(f"HTTP transport failure: {exc}") from exc
        except Exception as exc:
            exchange["error"] = _exception_text(exc)
            raise DecodeFailure(f"HTTP transport failure: {exc}") from exc

        try:
            response_text = response_body.decode("utf-8")
            parsed = json.loads(response_text)
            choices = parsed["choices"]
            if type(choices) is not list or len(choices) != 1:
                raise ValueError("response must contain exactly one choice")
            choice = choices[0]
            finish_reason = choice["finish_reason"]
            message = choice["message"]
            content = message["content"]
            if not isinstance(content, str):
                raise ValueError("assistant content must be a string")
            exchange["finish_reason"] = finish_reason
            exchange["raw_output"] = content
            exchange["usage"] = parsed.get("usage")
            exchange["response"]["json"] = parsed
            if finish_reason == "length":
                raise DecodeFailure(
                    "finish_reason=length: truncated JSON is never applied"
                )
            if finish_reason != "stop":
                raise ValueError(f"unsupported finish_reason: {finish_reason!r}")
            return content
        except DecodeFailure as exc:
            exchange["error"] = _exception_text(exc)
            raise
        except UnicodeDecodeError as exc:
            exchange["error"] = _exception_text(exc)
            raise DecodeFailure(f"response is not valid UTF-8: {exc}") from exc
        except Exception as exc:
            exchange["error"] = _exception_text(exc)
            raise DecodeFailure(f"invalid chat-completion response: {exc}") from exc


class _AuditedDecoder:
    """Write one local receipt for every actual decoder invocation."""

    def __init__(self, decoder, directory, *, clock, wall_clock):
        self.decoder = decoder
        self.directory = Path(directory)
        self.clock = clock
        self.wall_clock = wall_clock
        self.context = None
        self.receipts = []

    def set_context(self, call_index, episode_id, round_index):
        self.context = (call_index, episode_id, round_index)

    def __call__(self, prompt):
        if self.context is None:
            raise RuntimeError("missing scheduled-call context")
        call_index, episode_id, round_index = self.context
        started_at = self.wall_clock()
        started = self.clock()
        output = None
        error = None
        try:
            output = self.decoder(prompt)
            if not isinstance(output, str):
                raise TypeError("decoder must return a string")
            return output
        except Exception as exc:
            error = _exception_text(exc)
            raise
        finally:
            finished = self.clock()
            http = getattr(self.decoder, "last_http", None)
            receipt = {
                "schema_version": 1,
                "call_index": call_index,
                "episode_id": episode_id,
                "round_index": round_index,
                "started_at_unix": started_at,
                "elapsed_seconds": finished - started,
                "prompt": prompt,
                "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                "raw_output": (
                    output
                    if output is not None
                    else http.get("raw_output")
                    if isinstance(http, dict)
                    else None
                ),
                "decoder_error": error,
                "http": http,
            }
            path = self.directory / f"call-{len(self.receipts):04d}.json"
            _write_json(path, receipt, exclusive=True)
            self.receipts.append((path, receipt))


def _state_snapshot(register):
    return {
        "task_handles": sorted(register.task_handles),
        "defaults": [asdict(entry) for entry in register.defaults],
        **register.snapshot(),
    }


def _source_message(authored):
    # Deliberately enumerate the only three fields allowed across this boundary.
    return Message(
        message_id=authored.message_id,
        role=authored.role,
        text=authored.content,
    )


def _code_hashes():
    root = Path(__file__).resolve().parents[1]
    paths = {
        Path(__file__).resolve(),
        Path(maintenance_updater.__file__).resolve(),
        Path(maintenance_bank.__file__).resolve(),
        root / "src/stencil/focus/loop.py",
        root / "src/stencil/focus/register.py",
    }
    return {
        str(path.relative_to(root)): sha256_file(path)
        for path in sorted(paths, key=str)
    }


def _prepare_output(directory):
    root = Path(directory)
    if root.exists():
        if not root.is_dir() or any(root.iterdir()):
            raise FileExistsError("refuse existing nonempty output directory")
    else:
        root.mkdir(parents=True)
    (root / "calls").mkdir()
    return root


def _merge_error(error, extra):
    return extra if error is None else f"{error}; driver invariant: {extra}"


def run(
    input_path,
    output_dir,
    decoder,
    *,
    deadline_seconds=300.0,
    runtime_args=None,
    request_kind="code_answer",
    clock=time.monotonic,
    wall_clock=time.time,
):
    """Run exactly two eight-turn DEV trajectories, returning the final manifest."""
    if not callable(decoder):
        raise TypeError("decoder must be callable")
    if not isinstance(deadline_seconds, (int, float)) or deadline_seconds <= 0:
        raise ValueError("deadline_seconds must be positive")
    input_path = Path(input_path)
    allocation = maintenance_bank.load_authored_bank(
        input_path,
        expected_episodes=EXPECTED_EPISODES,
        expected_rounds=EXPECTED_ROUNDS,
    )
    if allocation.split != "dev":
        raise ValueError("DEV-only driver refuses non-DEV input")
    if request_kind != "code_answer" or any(
        episode.task.request_kinds != (request_kind,)
        for episode in allocation.episodes
    ):
        raise ValueError("DEV driver requires the registered code_answer kind")

    root = _prepare_output(output_dir)
    started_at = wall_clock()
    started = clock()
    deadline = started + float(deadline_seconds)
    if hasattr(decoder, "set_deadline"):
        decoder.set_deadline(deadline)
    audited = _AuditedDecoder(
        decoder, root / "calls", clock=clock, wall_clock=wall_clock
    )
    scheduled_turns = sum(len(episode.rounds) for episode in allocation.episodes)
    scheduled_views = sum(
        (len(episode.task.task_handles) + 1) * len(episode.task.request_kinds)
        for episode in allocation.episodes
        for _ in episode.rounds
    )
    manifest = {
        "schema_version": 1,
        "status": "INCOMPLETE",
        "reason": "run not completed",
        "started_at_unix": started_at,
        "finished_at_unix": None,
        "elapsed_seconds": None,
        "development_only": True,
        "fit_on": "none",
        "evaluated_on": "none",
        "gold_source": {"path": str(input_path), "sha256": sha256_file(input_path)},
        "code_sha256": _code_hashes(),
        "runtime_args": list(runtime_args) if runtime_args is not None else None,
        "runtime_config": {
            "deadline_seconds": float(deadline_seconds),
            "request_kind": request_kind,
            "request_timeout_ceiling_seconds": REQUEST_TIMEOUT_SECONDS,
            "receipt_reserve_seconds": RECEIPT_RESERVE_SECONDS,
            "workers": 0,
            "retries": 0,
        },
        "scheduled_episodes": EXPECTED_EPISODES,
        "scheduled_turns": scheduled_turns,
        "scheduled_views": scheduled_views,
        "recorded_turns": 0,
        "decoder_calls": 0,
        "rows_path": "rows.jsonl",
        "calls_path": "calls",
    }
    _write_json(root / "manifest.json", manifest)

    deadline_hit = False
    with (root / "rows.jsonl").open("x", encoding="utf-8") as rows_file:
        call_index = 0
        for episode in allocation.episodes:
            state = Register(task_handles=frozenset(episode.task.task_handles))
            past_messages = []
            for authored_round in episode.rounds:
                if clock() >= deadline - RECEIPT_RESERVE_SECONDS:
                    deadline_hit = True
                    break
                state = replace(state, generation=authored_round.index)
                source = _source_message(authored_round.messages[0])
                pre_state = _state_snapshot(state)
                before_receipts = len(audited.receipts)
                audited.set_context(
                    call_index, episode.episode_id, authored_round.index
                )
                prompt = None
                raw_output = None
                accepted_ops = ()
                error = None
                result = None
                pre_hash = None
                post_hash = None
                next_state = state
                try:
                    prepared = maintenance_updater.build_prompt(
                        register=state,
                        source=source,
                        past_messages=tuple(past_messages),
                        task_handles=episode.task.task_handles,
                        request_kind=request_kind,
                    )
                    prompt = prepared.text
                    pre_hash = prepared.base_state_sha256
                    result = maintenance_updater.execute(
                        register=state,
                        source=source,
                        decoder=audited,
                        past_messages=tuple(past_messages),
                        task_handles=episode.task.task_handles,
                        request_kind=request_kind,
                    )
                    raw_output = result.raw_response
                    error = result.error
                    accepted_ops = result.accepted_ops
                    pre_hash = result.pre_state_sha256
                    post_hash = result.post_state_sha256
                    candidate = result.register
                    if not isinstance(candidate, Register):
                        error = _merge_error(error, "updater returned non-Register")
                    elif result.prompt != prompt:
                        error = _merge_error(error, "execute/build_prompt mismatch")
                    elif result.pre_state_sha256 != prepared.base_state_sha256:
                        error = _merge_error(error, "pre-state hash mismatch")
                    elif result.error is not None and candidate != state:
                        error = _merge_error(
                            error, "rejected transaction changed state"
                        )
                    else:
                        candidate_hash = maintenance_updater.build_prompt(
                            register=candidate,
                            source=source,
                            past_messages=tuple(past_messages),
                            task_handles=episode.task.task_handles,
                            request_kind=request_kind,
                        ).base_state_sha256
                        if result.post_state_sha256 != candidate_hash:
                            error = _merge_error(error, "post-state hash mismatch")
                        elif error is None:
                            next_state = candidate
                except Exception as exc:
                    error = _exception_text(exc)

                receipt_delta = len(audited.receipts) - before_receipts
                if receipt_delta != 1:
                    error = _merge_error(
                        error, f"expected one decoder call, observed {receipt_delta}"
                    )
                    next_state = state
                    receipt_path = None
                    receipt = None
                else:
                    receipt_path, receipt = audited.receipts[-1]
                    if raw_output is None:
                        raw_output = receipt["raw_output"]
                if error is not None:
                    next_state = state
                    accepted_ops = ()
                if post_hash is None or error is not None:
                    post_hash = maintenance_updater.build_prompt(
                        register=next_state,
                        source=source,
                        past_messages=tuple(past_messages),
                        task_handles=episode.task.task_handles,
                        request_kind=request_kind,
                    ).base_state_sha256

                row = {
                    "schema_version": 1,
                    "call_index": call_index,
                    "episode_id": episode.episode_id,
                    "round_index": authored_round.index,
                    "generation": state.generation,
                    "source": {
                        "message_id": source.message_id,
                        "role": source.role,
                        "text": source.text,
                    },
                    "past_message_count": len(past_messages),
                    "task_handles": list(episode.task.task_handles),
                    "request_kind": request_kind,
                    "prompt": prompt,
                    "prompt_sha256": (
                        hashlib.sha256(prompt.encode()).hexdigest()
                        if prompt is not None
                        else None
                    ),
                    "raw_output": raw_output,
                    "pre_state": pre_state,
                    "post_state": _state_snapshot(next_state),
                    "pre_state_sha256": pre_hash,
                    "post_state_sha256": post_hash,
                    "accepted": error is None,
                    "accepted_ops": [asdict(entry) for entry in accepted_ops],
                    "error": error,
                    "token_usage": (
                        receipt["http"].get("usage")
                        if receipt is not None
                        and isinstance(receipt.get("http"), dict)
                        else None
                    ),
                    "elapsed_seconds": (
                        receipt["elapsed_seconds"] if receipt is not None else None
                    ),
                    "started_at_unix": (
                        receipt["started_at_unix"] if receipt is not None else None
                    ),
                    "call_receipt": (
                        str(receipt_path.relative_to(root))
                        if receipt_path is not None
                        else None
                    ),
                }
                _append_jsonl(rows_file, row)
                manifest["recorded_turns"] += 1
                manifest["decoder_calls"] = len(audited.receipts)
                _write_json(root / "manifest.json", manifest)
                state = next_state
                past_messages.append(source)
                call_index += 1
            if deadline_hit:
                break

    elapsed = clock() - started
    complete = (
        not deadline_hit
        and manifest["recorded_turns"] == scheduled_turns
        and manifest["decoder_calls"] == scheduled_turns
        and elapsed <= deadline_seconds
    )
    manifest.update(
        status="COMPLETE" if complete else "INCOMPLETE",
        reason=None
        if complete
        else "deadline before next scheduled turn"
        if deadline_hit
        else "scheduled trajectory or deadline incomplete",
        finished_at_unix=wall_clock(),
        elapsed_seconds=elapsed,
    )
    _write_json(root / "manifest.json", manifest)
    return manifest


def _parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:18088")
    parser.add_argument("--model", default="/model")
    parser.add_argument("--max-tokens", type=int, default=1024)
    parser.add_argument("--deadline-seconds", type=float, default=300.0)
    return parser


def main(argv=None):
    runtime_args = list(sys.argv[1:] if argv is None else argv)
    args = _parser().parse_args(runtime_args)
    decoder = ChatCompletionDecoder(args.base_url, args.model, args.max_tokens)
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
