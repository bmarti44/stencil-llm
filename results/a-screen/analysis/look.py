"""Distribution look at one or more arm record files -- not just J, but WHERE J fails.

The peer's saturation case (10 of 12 candidates at 100%, so the score had collapsed into
something else) is the failure this guards against: an aggregate in a healthy range can
still hide a metric that measures one narrow thing."""

import json
import sys
from collections import Counter, defaultdict

SUITES = (
    "functional",
    "regression",
    "contract",
    "support",
    "protected_function",
    "protected_contract",
)


def load(path):
    recs = defaultdict(dict)
    for line in open(path):
        d = json.loads(line)
        recs[d["session"]][d["request"]] = d
    return recs


def main(paths):
    for path in paths:
        recs = load(path)
        arm = next(iter(next(iter(recs.values())).values()))["arm"]
        done = {s: r for s, r in recs.items() if 1 in r and 2 in r}
        J = {
            s: bool(r[1]["scores"]["all"] and r[2]["scores"]["all"])
            for s, r in done.items()
        }
        FO = {
            s: bool(r[1]["scores"]["function_only"] and r[2]["scores"]["function_only"])
            for s, r in done.items()
        }
        print(f"\n===== {arm}  ({path})")
        print(f"complete sessions {len(done)}/48   J {sum(J.values())}/{len(done)}   "
              f"function-only {sum(FO.values())}/{len(done)}")

        # where does it fail?
        fail_at = Counter()
        fail_suite = Counter()
        terminal = Counter()
        for _s, r in done.items():
            for k in (1, 2):
                sc = r[k]["scores"]
                terminal[r[k]["terminal_reason"]] += 1
                if not sc["all"]:
                    fail_at[k] += 1
                    for n in SUITES:
                        if n in sc and not sc[n]:
                            fail_suite[n] += 1
        print("  failing checkpoint:", dict(fail_at))
        print("  failing suite     :", dict(fail_suite.most_common()))
        print("  terminal reason   :", dict(terminal.most_common()))
        print("  truncated         :",
              sum(1 for r in done.values() for k in (1, 2) if r[k]["truncated"]),
              " timed_out:",
              sum(1 for r in done.values() for k in (1, 2) if r[k]["timed_out"]))

        # is J concentrated in a few strata?
        for field in ("target_family", "support_family", "lifecycle", "rule_state"):
            tab = defaultdict(lambda: [0, 0])
            for s, r in done.items():
                key = r[1][field]
                tab[key][1] += 1
                tab[key][0] += int(J[s])
            print(f"  J by {field:15s}:",
                  "  ".join(f"{k}={v[0]}/{v[1]}" for k, v in sorted(tab.items())))

        toks = [r[k]["generated_tokens"] for r in done.values() for k in (1, 2)]
        if toks:
            toks.sort()
            print(f"  generated tokens  : min {toks[0]} median {toks[len(toks) // 2]} "
                  f"max {toks[-1]}  (cap 1536)")
        print("  per-session J     :",
              " ".join(f"{s}{'+' if J[s] else '-'}" for s in sorted(done)))


if __name__ == "__main__":
    main(sys.argv[1:])
