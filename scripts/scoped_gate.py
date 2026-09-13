"""Step 1 construction gate for the scoped-instruction diagnostic.

Astra's gate, verbatim: "gold and valid alternatives pass; every shortcut fails
its designated contrasts; source metadata cannot reach the automatic arm.
Failure here means repair the fixture before freezing it, not experiment on the
model."

Writes results/scoped/GATE.json.  Zero GPU, no benchmark data, no model.

    uv run python scripts/scoped_gate.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stencil.scoped_blocks import (  # noqa: E402
    BASELINE,
    LABEL_KEYS,
    POLICIES,
    REQUIRED_FIVE,
    RIVALS,
    SUITES,
    VALUES,
    arm_payload,
    block_digest,
    evaluate,
    gold_candidate,
    history_variant,
    passes,
    resolve,
    shortcut_candidate,
    value_candidate,
)
from stencil.scoped_dev_blocks import BLOCKS  # noqa: E402

ALT_STYLES = ("alt1", "alt2")
VARIANTS = ("revised", "direct", "irrelevant")


def gate(blocks=BLOCKS):
    problems, rows = [], []
    defeated_by = {p: [] for p in POLICIES}
    precedent_matches = 0
    ids = [b.id for b in blocks]
    if len(set(ids)) != len(ids):
        problems.append(f"duplicate block ids: {ids}")
    if len(blocks) != 16:
        problems.append(f"{len(blocks)} blocks, not 16")

    for block in blocks:
        want = []
        for case in block.cases:
            value, obs, ambiguous = resolve(block.history, case.path, case.fn_kind)
            want.append(value)
            if ambiguous:
                problems.append(f"{block.id}/{case.name}: resolution is a TIE -- "
                                "the measurement would depend on the tie-break")
            if block.precedent == value:
                precedent_matches += 1

            # 1. gold passes every suite
            scores = evaluate(block, case, gold_candidate(block, case))
            if not all(scores.values()):
                failed = [s for s in SUITES if not scores[s]]
                problems.append(f"{block.id}/{case.name}: GOLD fails {failed}")

            # 2. behaviourally identical alternatives pass too
            for style in ALT_STYLES:
                if not passes(block, case, gold_candidate(block, case, style)):
                    problems.append(
                        f"{block.id}/{case.name}: valid alternative {style} fails")

            # 3. the oracle is not vacuous: the two wrong values must fail
            for wrong in VALUES:
                if wrong == value:
                    continue
                if passes(block, case, value_candidate(block, case, wrong, obs)):
                    problems.append(f"{block.id}/{case.name}: the oracle ACCEPTS "
                                    f"{wrong!r} when {value!r} applies")

            # 4. the economics contrast: same final rule, three histories
            for variant in VARIANTS:
                alt = history_variant(block, variant)
                got = resolve(alt, case.path, case.fn_kind)[:2]
                if got != (value, obs):
                    problems.append(
                        f"{block.id}/{case.name}: history variant {variant} "
                        f"resolves to {got}, not {(value, obs)}")

            # 5. metadata isolation
            payload = json.dumps(arm_payload(block, case))
            blob = json.loads(payload)
            for key in LABEL_KEYS:
                if key in blob:
                    problems.append(f"{block.id}/{case.name}: arm payload leaks "
                                    f"{key!r}")
            leaked = [k for k in ("events", "applicable", "gold", "rule_turns",
                                  "defeats", "policy", "scope")
                      if k in blob or k in blob.get("request", {})]
            if leaked:
                problems.append(f"{block.id}/{case.name}: arm payload leaks {leaked}")

        if want[0] == want[1]:
            problems.append(f"{block.id}: both cases require {want[0]!r} -- the "
                            "matched pair does not discriminate")

        # 6. every claimed shortcut actually fails the BLOCK (both cases must
        #    succeed for a block to succeed)
        for policy in POLICIES:
            case_pass = [passes(block, case, shortcut_candidate(block, case, policy))
                         for case in block.cases]
            block_pass = all(case_pass)
            if not block_pass:
                defeated_by[policy].append(block.id)
            if policy in block.defeats and block_pass:
                problems.append(f"{block.id}: claims to defeat {policy} but it "
                                "PASSES the block")
            rows.append({"block": block.id, "policy": policy,
                         "cases": case_pass, "block_pass": block_pass,
                         "claimed": policy in block.defeats})

    # 7. all five required shortcuts refuted somewhere
    for policy in REQUIRED_FIVE:
        if not defeated_by[policy]:
            problems.append(f"no block defeats {policy}")

    # 7b. the scope-aware rivals are the anti-vacuity evidence: each must be
    #     refuted by at least one block AND survive at least one, or the matrix
    #     is just "the oracle refuses everything that is not gold".
    for policy in RIVALS:
        survived = len(blocks) - len(defeated_by[policy])
        if not defeated_by[policy]:
            problems.append(f"no block defeats the scope-aware rival {policy}")
        if not survived:
            problems.append(f"{policy} fails every block -- it cannot show that "
                            "the instrument discriminates between semantics")

    # 8. code precedent carries no signal about the answer.  The two cases of a
    #    block always require different values, so the precedent can agree with
    #    at most one of them.  What must not happen is that it systematically
    #    agrees with the same POSITION, or never agrees with one of them: either
    #    would make "copy the code that is already here" informative about which
    #    case is which.
    counts = {"A": 0, "B": 0, "neither": 0}
    for block in blocks:
        answers = [resolve(block.history, c.path, c.fn_kind)[0]
                   for c in block.cases]
        if block.precedent == answers[0]:
            counts["A"] += 1
        elif block.precedent == answers[1]:
            counts["B"] += 1
        else:
            counts["neither"] += 1
    if abs(counts["A"] - counts["B"]) > 2:
        problems.append(f"code precedent is position-biased: {counts}")
    if min(counts.values()) < 3:
        problems.append(f"code precedent is not counterbalanced: {counts}")

    return problems, rows, defeated_by, counts


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(ROOT / "results/scoped/GATE.json"))
    args = ap.parse_args(argv)

    problems, rows, defeated_by, counts = gate()
    out = {
        "blocks": [{"id": b.id, "family": b.family, "precedent": b.precedent,
                    "digest": block_digest(b),
                    "cases": [c.name for c in b.cases],
                    "answers": [resolve(b.history, c.path, c.fn_kind)[0]
                                for c in b.cases],
                    "defeats": list(b.defeats)} for b in BLOCKS],
        "defeated_by": {p: v for p, v in defeated_by.items()},
        "precedent_counterbalance": counts,
        "n_cases": 2 * len(BLOCKS),
        "baseline": BASELINE,
        "rows": rows,
        "problems": problems,
        "gate": "PASS" if not problems else "REFUSE",
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=1) + "\n")

    print(f"{'block':6} {'family':9} {'prec':8} {'case A -> B':28} defeats")
    for b in BLOCKS:
        ans = [resolve(b.history, c.path, c.fn_kind)[0] for c in b.cases]
        pair = f"{b.cases[0].name}={ans[0]} / {b.cases[1].name}={ans[1]}"
        print(f"{b.id:6} {b.family:9} {b.precedent:8} {pair:28} "
              f"{','.join(b.defeats)}")
    print()
    for policy in POLICIES:
        mark = ("required" if policy in REQUIRED_FIVE
                else "RIVAL   " if policy in RIVALS else "extra   ")
        print(f"{policy:16} {mark} defeated by {len(defeated_by[policy]):2}/16 "
              f"blocks: {' '.join(defeated_by[policy])}")
    print(f"\ncode precedent agrees with case A in {counts['A']} blocks, "
          f"case B in {counts['B']}, neither in {counts['neither']}")
    if problems:
        print(f"\nREFUSE -- {len(problems)} construction problems:")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("\nPASS -- gold and both valid alternatives pass every case; every "
          "claimed shortcut fails its block; no payload leaks source metadata")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
