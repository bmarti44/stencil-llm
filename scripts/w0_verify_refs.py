# ruff: noqa
"""W0.0 registered verification sweep: every train work's canonical
reference must parse, execute, satisfy every active obligation, trip no
stale obligation; records prompt length, target ids, and row alignment.
The builder freezes only at ZERO failures. feedback_mode=none prompts
(the registered neutral env text) are used for the length/alignment
records, matching training exactly. CPU + tokenizer only.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from tokenizers import Tokenizer

from stencil.t2_runner import score_work
from stencil.t2_sessions import generate_t2, prompt_at
from stencil.wave_ref import canonical_code

NEUTRAL = "[checker] (no feedback available this session)"
TRAIN = [13_400_000 + i for i in range(48)]

tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))


def main():
    failures, records = [], []
    for seed in TRAIN:
        sess = generate_t2(seed, 20, "dev", interference="s0")
        for wt in sess.work_turns:
            code = canonical_code(sess, wt)
            wr = score_work(code, sess, wt)
            bad = []
            if not wr.parse:
                bad.append("parse")
            if not wr.exec_ok:
                bad.append("exec")
            for o in sess.opportunities:
                if o.turn != wt:
                    continue
                e = wr.per_opportunity.get(o.opportunity_id, {})
                if o.cell == "active" and e.get("adherent") is not True:
                    bad.append(f"active:{o.moment_class}")
                if o.superseded and e.get("stale_action"):
                    bad.append(f"stale:{o.moment_class}")
            ptxt = prompt_at(sess, wt, "dev").replace(
                "[checker] (deterministic feedback on the previous submission is inserted here at run time)", NEUTRAL)
            p_ids = tok.encode(ptxt).ids
            t_ids = tok.encode(code).ids
            if bad:
                failures.append({"seed": seed, "wt": wt, "bad": bad})
            records.append({"seed": seed, "wt": wt, "prompt_len": len(p_ids),
                            "target_ids": t_ids, "n_target": len(t_ids),
                            "row_of_first_target": len(p_ids) - 1})
    out = {"n_works": len(records), "n_failures": len(failures), "failures": failures,
           "max_prompt_len": max(r["prompt_len"] for r in records),
           "max_total_len": max(r["prompt_len"] + r["n_target"] for r in records),
           "records": records}
    (ROOT / "results" / "qwen" / "w0-refs.json").write_text(json.dumps(out))
    print(f"{len(records)} works, {len(failures)} failures; max prompt {out['max_prompt_len']}, max total {out['max_total_len']}", flush=True)
    print("FROZEN" if not failures else f"NOT FROZEN: {failures[:5]}", flush=True)


if __name__ == "__main__":
    main()
