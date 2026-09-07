"""SLAB-2 DEV driver. CPU stubs and vLLM use the identical loop/executor path.

The GPU owner supplies an already-held vLLM server and its measured load time.
No model/server launch, process management, or evaluation content is performed.
Completion API: https://docs.vllm.ai/en/latest/serving/openai_compatible_server/
"""

import json
import time
from dataclasses import replace
from pathlib import Path
from urllib.request import Request as HTTPRequest
from urllib.request import urlopen

from stencil.focus import slab2_v2 as s
from stencil.focus.journal import Journal
from stencil.focus.loop import DecodeResult, Message, Session, generate_once
from stencil.focus.register import Register
from stencil.focus.renderer import Request, compact


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n")


class VLLMDecoder:
    """Token-ID completion transport; server must return actual generated IDs."""

    def __init__(self, endpoint, model, transport=None):
        self.endpoint, self.model = endpoint.rstrip("/"), model
        self.transport = transport or self._post

    def _post(self, payload):
        request = HTTPRequest(
            self.endpoint + "/completions",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urlopen(request, timeout=1200) as response:
            return json.load(response)

    def __call__(self, rendered):
        if len(rendered.prompt_ids) + s.REPLY_CAP > 32768:
            raise ValueError("context gate")
        started = time.monotonic()
        response = self.transport(
            dict(
                model=self.model,
                prompt=list(rendered.prompt_ids),
                max_tokens=s.REPLY_CAP,
                temperature=0,
                seed=20260906,
                return_token_ids=True,
                stop_token_ids=[151645, 151643],
            )
        )
        choice = response["choices"][0]
        ids = choice.get("token_ids")
        if ids is None or choice["finish_reason"] not in {"stop", "length"}:
            raise ValueError("vLLM requires token_ids and terminal finish_reason")
        if len(ids) != response["usage"]["completion_tokens"]:
            raise ValueError("vLLM token accounting mismatch")
        # loop appends EOS separately; keep it out of output_ids to avoid a
        # duplicated conversation terminator in every subsequent prompt.
        eos = None
        terminal_ids = {
            s.qwen_encode(token)[0] for token in ("<|im_end|>", "<|endoftext|>")
        }
        if choice["finish_reason"] == "stop" and ids and ids[-1] in terminal_ids:
            eos, ids = ids[-1], ids[:-1]
        if choice["finish_reason"] == "stop" and eos is None:
            raise ValueError("stop without terminal EOS token")
        return DecodeResult(
            choice["text"],
            tuple(ids),
            eos=eos,
            truncated=choice["finish_reason"] == "length",
            gpu_held_seconds=time.monotonic() - started,
        )


def run_lane(
    directory,
    episode,
    arm,
    decoder_factory,
    *,
    n_rounds=16,
    event_schedule=None,
    freeze_receipt=None,
):
    """Factory receives DEV episode/arm/turn; real adapter ignores these values."""
    s.validate_rounds(n_rounds)
    if (
        (
            episode.family != "dev"
            and freeze_receipt != episode.manifest()["episode_sha256"]
        )
        or len(episode.turns) != n_rounds
        or arm not in "RNTO"
        or len(arm) != 1
    ):
        raise ValueError("matching DEV lane required")
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=False)
    s.materialize(episode, root / "workspace", freeze_receipt)
    executor = s.Executor(root / "workspace", episode)
    session = Session(
        Register(defaults=episode.defaults, task_handles={"A", "B"}),
        Request("", "tool_call"),
        Journal(root / "loop.jsonl"),
    )
    rows, feedback = [], None
    for i, turn in enumerate(episode.turns):
        session.request = Request(
            "",
            "tool_call",
            turn.task,
            encode=s.qwen_encode,
            system=s.SYSTEM_PROMPT,
            max_tokens=32768 - s.REPLY_CAP,
            rule_mode=arm,
            rule_text=turn.t_text,
            template_id=episode.template_id,
        )
        messages = []
        if feedback is not None:
            messages.append(Message(f"tool{i}", "tool", "", tool_results=(feedback,)))
        events = turn.events if event_schedule is None else event_schedule[i]
        messages.append(
            Message(
                f"m{i}",
                "user",
                s.scoped_request(turn.request, turn, executor.last_parsable[turn.path]),
                events,
                adopted=True,
                confirmed_evidence=tuple(e.evidence for e in events if e.evidence),
            )
        )
        decoded = None
        prompt_tokens = None

        def decode(rendered, i=i):
            nonlocal decoded, prompt_tokens
            prompt_tokens = len(rendered.prompt_ids)
            if prompt_tokens + s.REPLY_CAP > 32768:
                raise ValueError("context gate")
            decoded = decoder_factory(episode, arm, i)(rendered)
            if (
                not isinstance(decoded, DecodeResult)
                or decoded.truncated is None
                or decoded.output_ids is None
            ):
                raise ValueError("decoder must report truncation and output IDs")
            return decoded

        output, _ = generate_once(session, messages, decode)
        output, feedback, attempts = submit(
            session,
            decode=decode,
            executor=executor,
            turn=i,
            output=output,
            decoded=lambda: decoded,  # noqa: B023 (synchronous repair in this round)
        )
        row = dict(
            episode_id=episode.episode_id,
            arm=arm,
            turn=i,
            **attempt_fields(attempts, turn),
            output=output,
            output_ids=list(decoded.output_ids),
            truncated=decoded.truncated,
            output_tokens=len(decoded.output_ids) + int(decoded.eos is not None),
            eos=decoded.eos,
            prompt_tokens=prompt_tokens,
            execution=feedback,
            outcome=s.check(episode, i, executor, eligible_traits=None),
        )
        with (root / "raw.jsonl").open("a") as stream:
            stream.write(compact(row) + "\n")
        rows.append(row)
    return dict(
        episode_id=episode.episode_id,
        arm=arm,
        records=rows,
        output_tokens=sum(row["output_tokens"] for row in rows),
    )


def run_q(
    directory, episode, arm, decoder_factory, *, n_rounds=16, freeze_receipt=None
):
    """Every scheduled task independently, with correct prerequisite files."""
    s.validate_rounds(n_rounds)
    if arm != "Q" or len(episode.turns) != n_rounds:
        raise ValueError("matching Q schedule required")
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=False)
    gold = Register(defaults=episode.defaults, task_handles={"A", "B"})
    files = dict(episode.initial)
    rows = []
    for i, turn in enumerate(episode.turns):
        gold = gold.apply(turn.events)
        workspace = root / str(i)
        s.materialize(episode, workspace, freeze_receipt)
        for name, body in files.items():
            (workspace / name).write_text(body)
        executor = s.Executor(workspace, episode)
        executor.last_parsable = dict(files)
        # Only live rules: no stale lifecycle messages, tombstones, or history.
        live = gold.live(turn.task, "tool_call")
        fresh = Register(
            defaults=tuple(
                replace(v.entry, action="add", target_version=None, evidence=None)
                for v in live
            ),
            task_handles={"A", "B"},
        )
        session = Session(
            fresh,
            Request(
                "",
                "tool_call",
                turn.task,
                system=s.SYSTEM_PROMPT,
                encode=s.qwen_encode,
                max_tokens=32768 - s.REPLY_CAP,
            ),
            Journal(root / f"q-{i}.jsonl"),
        )
        request = s.scoped_request(
            turn.request.split("\n", 1)[-1], turn, files[turn.path]
        )
        result = None
        prompt_tokens = None

        def decode(rendered, i=i):
            nonlocal result, prompt_tokens
            prompt_tokens = len(rendered.prompt_ids)
            result = decoder_factory(episode, "Q", i)(rendered)
            if result.truncated is None or result.output_ids is None:
                raise ValueError("Q decoder requires cap and token accounting")
            return result

        output, _ = generate_once(session, [Message(f"q{i}", "user", request)], decode)
        output, feedback, attempts = submit(
            session,
            decode=decode,
            executor=executor,
            turn=i,
            output=output,
            decoded=lambda: result,  # noqa: B023 (synchronous repair in this round)
        )
        row = dict(
            episode_id=episode.episode_id,
            arm="Q",
            turn=i,
            **attempt_fields(attempts, turn),
            execution=feedback,
            output=output,
            output_ids=list(result.output_ids),
            eos=result.eos,
            truncated=result.truncated,
            prompt_tokens=prompt_tokens,
            output_tokens=len(result.output_ids) + int(result.eos is not None),
            outcome=s.check(episode, i, executor, eligible_traits=tuple(s.TRAITS)),
        )
        rows.append(row)
        with (root / "raw.jsonl").open("a") as stream:
            stream.write(compact(row) + "\n")
        path, body, _ = s.parse_reply(s.reference(episode, i), turn.path)
        files[path] = body
    return dict(
        episode_id=episode.episode_id,
        arm="Q",
        records=rows,
        qualified=all(r["outcome"]["success"] for r in rows),
        output_tokens=sum(r["output_tokens"] for r in rows),
    )


def submit(session, *, decode, executor, turn, output, decoded):
    attempts = []
    for attempt in range(2):
        result = decoded()
        feedback = executor.run(output, turn, truncated=result.truncated)
        attempts.append(
            dict(
                output=output,
                output_ids=list(result.output_ids),
                eos=result.eos,
                truncated=result.truncated,
                execution=dict(feedback),
            )
        )
        write(executor.directory / f"attempts-{turn}.json", attempts)
        if feedback.get("category") != "syntax_error" or attempt == 1:
            break
        diagnostic = (
            f"{feedback['syntax_type']}: {feedback['error']}\n"
            f"Offending line {feedback['lineno']}:\n{feedback['offending_line']}"
            "\nOne syntax repair attempt remains. Correct and resubmit ONLY "
            "the same requested function and its report trailer."
        )
        output, _ = generate_once(
            session, [Message(f"repair-{turn}", "user", diagnostic)], decode
        )
    return output, feedback, attempts


def attempt_fields(attempts, turn):
    return dict(
        attempts=attempts,
        repairs_used=len(attempts) - 1,
        indent_attempted=any(s.attempted(a["output"], turn) for a in attempts),
        total_output_tokens=sum(
            len(a["output_ids"]) + int(a["eos"] is not None) for a in attempts
        ),
    )


def stub_factory(episode, arm, turn):
    def decode(rendered):
        t = episode.turns[turn]
        path, code, report = s.parse_reply(s.reference(episode, turn), t.path)
        import ast

        node = next(
            n
            for n in ast.parse(code).body
            if isinstance(n, ast.FunctionDef) and n.name == t.function
        )
        code = "".join(
            code.splitlines(keepends=True)[node.lineno - 1 : node.end_lineno]
        )
        output = f"```python {path}\n{code}```\nreport: " + " ".join(
            f"{k}={v}" for k, v in report.items()
        )
        return DecodeResult(
            output, tuple(s.qwen_encode(output)), eos=151645, truncated=False
        )

    return decode
