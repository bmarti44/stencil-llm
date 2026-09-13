"""Per-message token counts for candidate-A sessions under the shipping tokenizer.

Usage: uv run python scripts/a_screen_tokens.py S02 [S03 ...]   (authoring aid; prints
the prompt total at each live request and the per-message counts so prefixes can be
sized for the registered compaction requirement).
"""

from __future__ import annotations

import argparse


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("slots", nargs="+")
    ap.add_argument("--hub", default="deploy/stencil_focus/build/hub-4b")
    a = ap.parse_args()
    from transformers import AutoTokenizer

    from stencil import a_screen as A
    from stencil.a_screen_pool import load

    tok = AutoTokenizer.from_pretrained(a.hub, trust_remote_code=True)
    count = A.make_counter(tok)
    for slot in a.slots:
        s = load(slot)
        m1 = A.session_messages(s, 1, dict(s.files))
        f1 = A.gold_files(s, 1)
        m2 = A.session_messages(s, 2, f1, A.gold_reply(s, 1), {s.requests[0].target})
        per = [count([m]) for m in m2]
        _, idx1 = A.pack(m1, count)
        _, idx2 = A.pack(m2, count)
        print(
            f"{slot} total@req1={count(m1)} total@req2={count(m2)} "
            f"budget={A.PROMPT_BUDGET}"
        )
        print(f"  per-message: {per}")
        print(
            f"  prefix={sum(per[1:17])} req1={per[17]} reply1={per[18]} "
            f"event={per[19]} req2={per[20]}"
        )
        print(
            f"  surviving prefix turns @req1={sorted(A.surviving_prefix_turns(idx1))} "
            f"@req2={sorted(A.surviving_prefix_turns(idx2))} rule_turns={s.rule_turns}"
        )


if __name__ == "__main__":
    main()
