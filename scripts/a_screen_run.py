# ruff: noqa: E501
"""Run one arm of the candidate-A screen over the SCREEN pool (registration §3, §5, §6, §9).

For every session: pack the live request 1 (system + newest whole turns that fit in
2,560 tokens), generate greedily (thinking disabled, <= 1,536 new tokens, 300 s deadline),
apply the reply to the arm's own repository, score every applicable suite; then build
request 2 from that repository with the verbatim first reply and the lifecycle event in
history, generate, apply, score.  One record per request is appended as it completes
(resumable at session granularity).  ``off`` loads no adapter; ``sft``/``cf`` load the
adapter directory (unmerged LoRA on the same frozen trunk).

Usage (through tools/gpu_reserve.sh):
  uv run python scripts/a_screen_run.py --arm cf --adapter results/a-screen/adapters/cf \
      --out results/a-screen/runs/cf.jsonl
Pilot: ``--slots S02,S05,S09,S13`` (maximum-context timing, registration §8).
"""

from __future__ import annotations

import argparse
import functools
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stencil import a_screen as A  # noqa: E402
from stencil.a_screen_pool import screen_sessions  # noqa: E402

print = functools.partial(print, flush=True)  # noqa: A001


def repo_hash(files: dict[str, str]) -> str:
    body = json.dumps(files, sort_keys=True)
    return hashlib.sha256(body.encode()).hexdigest()[:16]


def failed_scores(state: str) -> dict:
    return {
        "state": state,
        "functional": False,
        "regression": False,
        "contract": False,
        "support": False,
        "all": False,
        "function_only": False,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", choices=["off", "sft", "cf"], required=True)
    ap.add_argument("--adapter", default="")
    ap.add_argument("--out", required=True)
    ap.add_argument("--hub", default=str(ROOT / "deploy/stencil_focus/build/hub-4b"))
    ap.add_argument("--max-new", type=int, default=A.MAX_NEW_TOKENS)
    ap.add_argument("--deadline", type=float, default=300.0)
    ap.add_argument("--slots", default="", help="comma-separated subset (pilot)")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    if a.arm != "off" and not a.adapter:
        ap.error("--adapter is required for sft/cf")
    if a.arm == "off" and a.adapter:
        ap.error("off takes no adapter")

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    torch.manual_seed(0)
    tok = AutoTokenizer.from_pretrained(a.hub, trust_remote_code=True)
    count = A.make_counter(tok)
    model = AutoModelForCausalLM.from_pretrained(
        a.hub, trust_remote_code=True, dtype=torch.bfloat16, device_map="cuda"
    )
    if a.adapter:
        from peft import PeftModel

        model = PeftModel.from_pretrained(model, a.adapter)
    model.eval()
    eos_cfg = model.config.eos_token_id
    eos = list(eos_cfg if isinstance(eos_cfg, list) else [eos_cfg])
    im_end = tok.convert_tokens_to_ids("<|im_end|>")
    if im_end not in eos:
        eos.append(im_end)

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out.exists():
        for line in out.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                if r["request"] == 2:
                    done.add(r["session"])

    sessions = screen_sessions()
    if a.slots:
        want = set(a.slots.split(","))
        sessions = [s for s in sessions if s.id in want]
    if a.limit:
        sessions = sessions[: a.limit]

    def generate(msgs: list[dict]) -> dict:
        packed, kept = A.pack(msgs, count)
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
                max_time=a.deadline,
            )
        secs = time.time() - t0
        new = gen[0, ids.shape[1] :].tolist()
        ended = bool(new) and new[-1] in eos
        truncated = len(new) >= a.max_new and not ended
        timed_out = secs >= a.deadline and not ended
        text = tok.decode([t for t in new if t not in eos], skip_special_tokens=True)
        return {
            "prompt": prompt,
            "kept_indices": kept,
            "surviving_prefix_turns": sorted(A.surviving_prefix_turns(kept)),
            "prompt_tokens": int(ids.shape[1]),
            "generated_tokens": len(new),
            "truncated": truncated,
            "timed_out": timed_out,
            "seconds": secs,
            "output": text,
        }

    n = n_j = n_f = 0
    for s in sessions:
        if s.id in done:
            continue
        files0 = dict(s.files)
        recs = []
        # ---- checkpoint 1
        g1 = generate(A.session_messages(s, 1, files0))
        reason = (
            "truncated"
            if g1["truncated"]
            else "timeout"
            if g1["timed_out"]
            else "applied"
        )
        files1, apply_reason = (
            (None, reason)
            if reason != "applied"
            else A.apply_reply(files0, s.requests[0], g1["output"])
        )
        if files1 is None:
            sc1 = failed_scores(s.state_at[0])
            files1 = files0
        else:
            sc1 = A.score_checkpoint(s, 1, files1)
        recs.append(
            {
                "session": s.id,
                "arm": a.arm,
                "request": 1,
                "target_family": s.target_family,
                "support_family": s.support_family,
                "lifecycle": s.lifecycle,
                "rule_state": s.state_at[0],
                "repo_before": repo_hash(files0),
                "repo_after": repo_hash(files1),
                "terminal_reason": apply_reason,
                **g1,
                "scores": sc1,
            }
        )
        # ---- checkpoint 2 (on the arm's own repository, its own verbatim first reply)
        changed = {p for p in files1 if files1[p] != files0.get(p)}
        g2 = generate(A.session_messages(s, 2, files1, g1["output"], changed))
        reason = (
            "truncated"
            if g2["truncated"]
            else "timeout"
            if g2["timed_out"]
            else "applied"
        )
        files2, apply_reason = (
            (None, reason)
            if reason != "applied"
            else A.apply_reply(files1, s.requests[1], g2["output"])
        )
        if files2 is None:
            sc2 = failed_scores(s.state_at[1])
            files2 = files1
        else:
            sc2 = A.score_checkpoint(s, 2, files2)
        J = bool(sc1["all"] and sc2["all"])
        fo = bool(sc1["function_only"] and sc2["function_only"])
        recs.append(
            {
                "session": s.id,
                "arm": a.arm,
                "request": 2,
                "target_family": s.target_family,
                "support_family": s.support_family,
                "lifecycle": s.lifecycle,
                "rule_state": s.state_at[1],
                "repo_before": repo_hash(files1),
                "repo_after": repo_hash(files2),
                "terminal_reason": apply_reason,
                **g2,
                "scores": sc2,
                "J": J,
                "function_only": fo,
            }
        )
        with out.open("a") as fh:
            for r in recs:
                fh.write(json.dumps(r) + "\n")
        n += 1
        n_j += int(J)
        n_f += int(fo)
        print(
            f"[{s.id} {a.arm}] J={J} fo={fo} | @1 {sc1['all']} ({g1['generated_tokens']} tok, {g1['seconds']:.0f}s, {apply_reason if False else recs[0]['terminal_reason']}) "
            f"| @2 {sc2['all']} ({g2['generated_tokens']} tok, {g2['seconds']:.0f}s, {apply_reason}) | running J {n_j}/{n} fo {n_f}/{n}"
        )
    print(f"DONE arm={a.arm} new={n} J={n_j} function_only={n_f}")


if __name__ == "__main__":
    main()
