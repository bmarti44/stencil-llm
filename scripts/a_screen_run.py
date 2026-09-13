# ruff: noqa: E501
"""Run one arm of the candidate-A screen over the SCREEN pool (registration §3, §5, §6, §9).

For every session: pack live request 1 (system + newest whole turns inside the prompt
budget), generate greedily (thinking disabled, <= MAX_NEW_TOKENS, 300 s deadline), apply
the reply to the arm's own repository, score every applicable suite; then build request 2
from that repository with the verbatim first reply and the lifecycle event in history,
generate, apply, score.  EVERY request is written to the record file as it completes, so a
run resumes at request granularity (a half-finished session resumes at request 2 from the
saved reply).  ``off`` loads no adapter; ``sft``/``cf`` load the adapter directory
(unmerged LoRA on the same frozen trunk).

Amendment 1 (Astra implementation review): deterministic execution settings are imported
before torch; the shipping generation config's terminal tokens are all honoured; a
generation that passes the deadline fails even if it ended; the frozen pool hash is
verified before any generation; each record carries the implementation, model and adapter
identities; and the run stops starting new sessions when its cumulative GPU budget is
spent (``--budget-min``), recording INCOMPLETE rather than overrunning.

Usage (through tools/gpu_reserve.sh):
  uv run python scripts/a_screen_run.py --arm cf --adapter results/a-screen/adapters/cf \
      --out results/a-screen/runs/cf.jsonl --budget-min 45
Pilot: ``--longest 4`` (the registered maximum-context pilot, §8).
"""

from __future__ import annotations

import argparse
import functools
import hashlib
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import stencil.determinism  # noqa: E402, F401  (sets CUBLAS workspace before torch)
from stencil import a_screen as A  # noqa: E402
from stencil.a_screen_pool import screen_sessions  # noqa: E402

print = functools.partial(print, flush=True)  # noqa: A001

FREEZE = ROOT / "results/a-screen/screen-pool.json"


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def repo_hash(files: dict[str, str]) -> str:
    return sha(json.dumps(files, sort_keys=True))


def verify_frozen(sessions) -> str:
    """Astra F15: refuse to run unless every session matches the frozen record."""
    frozen = json.loads(FREEZE.read_text())
    slots = frozen["slots"]
    assert len(sessions) == frozen["n"], (
        f"{len(sessions)} sessions, frozen {frozen['n']}"
    )
    for s in sessions:
        want = slots[s.id]["content_sha256"]
        got = sha(json.dumps(asdict(s), sort_keys=True))
        assert got == want, f"{s.id}: content {got}, frozen {want}"
    return frozen["pool_sha256"]


def failed_scores(state: str) -> dict:
    out = {"state": state, "api_preserved": False, "api_msg": "not applied"}
    for name in A.SUITES:
        out[name] = False
    out["all"] = False
    out["function_only"] = False
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", choices=["off", "sft", "cf"], required=True)
    ap.add_argument("--adapter", default="")
    ap.add_argument("--out", required=True)
    ap.add_argument("--hub", default=str(ROOT / "deploy/stencil_focus/build/hub-4b"))
    ap.add_argument("--max-new", type=int, default=A.MAX_NEW_TOKENS)
    ap.add_argument("--deadline", type=float, default=300.0)
    ap.add_argument("--slots", default="", help="comma-separated subset")
    ap.add_argument(
        "--longest", type=int, default=0, help="pilot: the N longest-prompt sessions"
    )
    ap.add_argument(
        "--budget-min",
        type=float,
        default=0.0,
        help="stop starting sessions after this many minutes (0 = no limit)",
    )
    a = ap.parse_args()
    if a.arm != "off" and not a.adapter:
        ap.error("--adapter is required for sft/cf")
    if a.arm == "off" and a.adapter:
        ap.error("off takes no adapter")
    adapter_steps = None
    if a.adapter:
        # Astra F13: the registered quantity is the adapter at the FINAL COMPLETED optimizer
        # step of one uninterrupted allocation.  The trainer also writes periodic crash
        # checkpoints marked status=running/final=false; refuse those.  Checked before the
        # model load so a wrong adapter costs no GPU time.
        tl = Path(a.adapter) / "train-log.json"
        if not tl.exists():
            ap.error(
                f"{a.adapter}: no train-log.json; cannot verify the adapter is final"
            )
        tlog = json.loads(tl.read_text())
        if not (tlog.get("final") is True and tlog.get("status") == "complete"):
            ap.error(
                f"{a.adapter}: train-log says final={tlog.get('final')} "
                f"status={tlog.get('status')}; only a final adapter may be evaluated"
            )
        if tlog.get("objective") != a.arm:
            ap.error(
                f"{a.adapter}: trained objective {tlog.get('objective')!r} "
                f"does not match arm {a.arm!r}"
            )
        adapter_steps = tlog.get("steps")
    t_start = time.time()

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig

    torch.manual_seed(0)
    tok = AutoTokenizer.from_pretrained(a.hub, trust_remote_code=True)
    count = A.make_counter(tok)
    model = AutoModelForCausalLM.from_pretrained(
        a.hub, trust_remote_code=True, dtype=torch.bfloat16, device_map="cuda"
    )
    adapter_id = "none"
    if a.adapter:
        from peft import PeftModel

        model = PeftModel.from_pretrained(model, a.adapter)
        weights = Path(a.adapter) / "adapter_model.safetensors"
        adapter_id = sha(weights.read_bytes().hex()) if weights.exists() else "missing"
    model.eval()

    # Astra F4: every terminal token the shipping package declares, not just config.eos
    gen_cfg = GenerationConfig.from_pretrained(a.hub)
    eos = set()
    for source in (gen_cfg.eos_token_id, model.config.eos_token_id):
        if source is None:
            continue
        eos |= set(source if isinstance(source, list) else [source])
    im_end = tok.convert_tokens_to_ids("<|im_end|>")
    if im_end is not None:
        eos.add(im_end)
    eos = sorted(eos)

    sessions = screen_sessions()
    pool_sha = verify_frozen(sessions)
    identity = {
        "pool_sha256": pool_sha,
        "a_screen_sha256": sha((ROOT / "src/stencil/a_screen.py").read_text()),
        "contracts_sha256": sha((ROOT / "src/stencil/contracts.py").read_text()),
        "runner_sha256": sha(Path(__file__).read_text()),
        "hub": str(a.hub),
        "adapter": a.adapter or "none",
        "adapter_sha256": adapter_id,
        "adapter_steps": adapter_steps,
        "eos": eos,
        "max_new": a.max_new,
        "prompt_budget": A.PROMPT_BUDGET,
    }
    print("identity " + json.dumps(identity))

    if a.slots:
        want = set(a.slots.split(","))
        sessions = [s for s in sessions if s.id in want]
    if a.longest:
        # Astra F14: the registered pilot is the longest-prompt sessions on the gold path
        def prompt_max(s):
            m1 = A.session_messages(s, 1, dict(s.files))
            f1 = A.gold_files(s, 1)
            m2 = A.session_messages(s, 2, dict(s.files), A.gold_reply(s, 1), f1)
            return max(
                count(A.pack(m1, count)[0]),
                count(A.pack(m2, count, drop_first=A.drop_first_order(2))[0]),
            )

        sessions = sorted(sessions, key=prompt_max, reverse=True)[: a.longest]
        print("pilot sessions " + ",".join(s.id for s in sessions))

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    # Astra F3: resume per request, and only from records of THIS arm and identity
    done: dict[str, dict] = {}
    if out.exists():
        for line in out.read_text().splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                print("skipping a malformed record line")
                continue
            if r.get("arm") != a.arm:
                continue
            if r.get("identity", {}).get("adapter_sha256") != adapter_id:
                continue
            done[f"{r['session']}:{r['request']}"] = r

    def generate(msgs: list[dict], checkpoint: int, session) -> dict:
        packed, kept = A.pack(msgs, count, drop_first=A.drop_first_order(checkpoint))
        # Astra F1: required messages must be in the window before we generate
        missing = A.required_indices(session, checkpoint) - set(kept)
        assert not missing, (
            f"{session.id}@{checkpoint}: required messages dropped {sorted(missing)}"
        )
        prompt = A.render_prompt(tok, packed)
        ids = tok(prompt, return_tensors="pt", add_special_tokens=False).input_ids.to(
            model.device
        )
        assert ids.shape[1] <= A.PROMPT_BUDGET, ids.shape
        t0 = time.time()
        with torch.no_grad():
            gen = model.generate(
                ids,
                attention_mask=torch.ones_like(ids),
                max_new_tokens=a.max_new,
                do_sample=False,
                eos_token_id=eos,
                pad_token_id=gen_cfg.pad_token_id,
                max_time=a.deadline,
            )
        secs = time.time() - t0
        new = gen[0, ids.shape[1] :].tolist()
        ended = bool(new) and new[-1] in eos
        truncated = len(new) >= a.max_new and not ended
        over_deadline = secs >= a.deadline  # Astra F4: a late EOS is still a failure
        text = tok.decode([t for t in new if t not in eos], skip_special_tokens=True)
        return {
            "prompt": prompt,
            "kept_indices": kept,
            "surviving_prefix_turns": sorted(A.surviving_prefix_turns(kept)),
            "prompt_tokens": int(ids.shape[1]),
            "generated_tokens": len(new),
            "ended_on_eos": ended,
            "truncated": truncated,
            "timed_out": over_deadline,
            "seconds": secs,
            "output": text,
        }

    def terminal(gen: dict) -> str:
        if gen["truncated"]:
            return "truncated"
        if gen["timed_out"]:
            return "deadline_exceeded"
        return "applied"

    def write(rec: dict) -> None:
        with out.open("a") as fh:
            fh.write(json.dumps(rec) + "\n")
            fh.flush()

    n = n_j = n_f = 0
    incomplete = []
    for s in sessions:
        k1 = f"{s.id}:1"
        k2 = f"{s.id}:2"
        if k2 in done:
            continue
        spent = (time.time() - t_start) / 60
        if a.budget_min and spent >= a.budget_min and k1 not in done:
            incomplete.append(s.id)
            continue
        files0 = dict(s.files)
        # ---- checkpoint 1 (reuse a saved request-1 record when resuming)
        if k1 in done:
            rec1 = done[k1]
            g1 = {k: rec1[k] for k in ("output", "seconds", "generated_tokens")}
            reason1 = rec1["terminal_reason"]
            sc1 = rec1["scores"]
            files1 = files0 if reason1 != "applied" else None
            if reason1 == "applied":
                files1, _ = A.apply_reply(files0, s.requests[0], rec1["output"])
                if files1 is None:
                    files1 = files0
        else:
            g1 = generate(A.session_messages(s, 1, files0), 1, s)
            reason1 = terminal(g1)
            files1, apply1 = (
                (None, reason1)
                if reason1 != "applied"
                else A.apply_reply(files0, s.requests[0], g1["output"])
            )
            reason1 = apply1
            if files1 is None:
                sc1 = failed_scores(s.state_at[0])
                files1 = files0
            else:
                sc1 = A.score_checkpoint(s, 1, files1)
            write(
                {
                    "session": s.id,
                    "arm": a.arm,
                    "request": 1,
                    "project": s.project,
                    "target_family": s.target_family,
                    "support_family": s.support_family,
                    "lifecycle": s.lifecycle,
                    "rule_state": s.state_at[0],
                    "repo_before": repo_hash(files0),
                    "repo_after": repo_hash(files1),
                    "terminal_reason": reason1,
                    "identity": identity,
                    **g1,
                    "scores": sc1,
                }
            )
        # ---- checkpoint 2 on the arm's own repository and its verbatim first reply
        g2 = generate(A.session_messages(s, 2, files0, g1["output"], files1), 2, s)
        reason2 = terminal(g2)
        files2, apply2 = (
            (None, reason2)
            if reason2 != "applied"
            else A.apply_reply(files1, s.requests[1], g2["output"])
        )
        reason2 = apply2
        if files2 is None:
            sc2 = failed_scores(s.state_at[1])
            files2 = files1
        else:
            sc2 = A.score_checkpoint(s, 2, files2)
        J = bool(sc1["all"] and sc2["all"])
        fo = bool(sc1["function_only"] and sc2["function_only"])
        write(
            {
                "session": s.id,
                "arm": a.arm,
                "request": 2,
                "project": s.project,
                "target_family": s.target_family,
                "support_family": s.support_family,
                "lifecycle": s.lifecycle,
                "rule_state": s.state_at[1],
                "repo_before": repo_hash(files1),
                "repo_after": repo_hash(files2),
                "terminal_reason": reason2,
                "identity": identity,
                **g2,
                "scores": sc2,
                "J": J,
                "function_only": fo,
            }
        )
        n += 1
        n_j += int(J)
        n_f += int(fo)
        print(
            f"[{s.id} {a.arm}] J={J} fo={fo} | @1 {sc1['all']} ({g1['generated_tokens']} tok, "
            f"{g1['seconds']:.0f}s, {reason1}) | @2 {sc2['all']} ({g2['generated_tokens']} tok, "
            f"{g2['seconds']:.0f}s, {reason2}) | running J {n_j}/{n} fo {n_f}/{n} | "
            f"{(time.time() - t_start) / 60:.0f} min"
        )
    status = "INCOMPLETE" if incomplete else "COMPLETE"
    print(
        f"DONE arm={a.arm} new={n} J={n_j} function_only={n_f} minutes="
        f"{(time.time() - t_start) / 60:.1f} status={status}"
        + (f" not_started={','.join(incomplete)}" if incomplete else "")
    )


if __name__ == "__main__":
    main()
