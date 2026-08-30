# ruff: noqa
"""PRESS-PLAN T0.2: offline score-policy matrix over the T0.1 trace.

Definitions (registered):
- active event: cell == "active";
- correct selection: chosen candidate has source "live" and the event's
  pred_type;
- false selection (pre-structural-guard, plan v3.1): a press decision
  (score > threshold) at a non-active event, OR at an active event with
  a non-live chosen candidate;
- session trial fails if any false selection occurs in it;
- threshold selection on TRACE negatives PLUS registered counterfeit
  hard negatives (G0 ruling: live same-type candidates stripped from
  active events — the shape of a conflicting-note-at-inactive-moment):
  per family, the max-recall threshold among those with <= 2 false
  sessions of 48; ties -> higher threshold, enumerated at exact score
  boundaries via nextafter (G0 sol HIGH: the old `uniq[0]-1.0` froze
  cosine at -0.359 instead of just below 0.641). AUPRC is active vs ALL
  events including -inf abstentions (ranked at the bottom), plus a
  separate hard-negative AUPRC — the registered secondary tie-break.
  No guarantee is claimed from trace data; certification happens once,
  sealed, on a fixture block.
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil.press_families import FAMILIES, counterfeit_hard_negative, evaluate_event
from stencil.t2_trace import load_trace


def auprc(pairs):
    """pairs: (score, is_positive), ranked by score desc; average precision."""
    pairs = sorted(pairs, key=lambda x: -x[0])
    tp = fp = 0
    npos = sum(1 for _, y in pairs if y)
    if npos == 0:
        return 0.0
    ap = 0.0
    for s, y in pairs:
        if y:
            tp += 1
            ap += tp / (tp + fp)
        else:
            fp += 1
    return ap / npos


def main():
    tr = load_trace(ROOT / "results" / "qwen" / "t0-trace.pt")
    events = tr["events"]
    n_active = sum(1 for e in events if e["cell"] == "active")
    sessions = sorted({e["seed"] for e in events})
    report = {"n_events": len(events), "n_active": n_active, "n_sessions": len(sessions)}
    print(f"{len(events)} events ({n_active} active) across {len(sessions)} sessions", flush=True)

    counterfeits = [hn for hn in (counterfeit_hard_negative(e) for e in events if e["cell"] == "active") if hn is not None]
    print(f"{len(counterfeits)} counterfeit hard negatives constructed", flush=True)

    for fam in FAMILIES:
        evald = []
        for e in events:
            s, j = evaluate_event(fam, e)
            correct = j is not None and e["candidates"][j]["source"] == "live" and e["candidates"][j]["type"] == e["pred_type"]
            evald.append({"seed": e["seed"], "score": s, "chosen_ok": correct, "active": e["cell"] == "active", "hard": False})
        for hn in counterfeits:
            s, j = evaluate_event(fam, hn)
            evald.append({"seed": hn["seed"], "score": s, "chosen_ok": False, "active": False, "hard": True})
        uniq = sorted({x["score"] for x in evald if x["score"] != float("-inf")})
        cands_t = sorted(set(uniq) | {math.nextafter(s, -math.inf) for s in uniq}) if uniq else [0.0]
        best = None
        for t in cands_t:
            rec_n = sum(1 for x in evald if x["active"] and x["score"] > t and x["chosen_ok"])
            false_sessions = len({x["seed"] for x in evald if x["score"] > t and not (x["active"] and x["chosen_ok"])})
            rec = rec_n / max(1, n_active)
            if false_sessions <= 2 and (best is None or rec > best["recall"] or (rec == best["recall"] and t > best["threshold"])):
                best = {"threshold": t, "recall": rec, "false_sessions": false_sessions}
        if best is None:
            best = {"threshold": None, "recall": 0.0, "false_sessions": None}
        best["auprc_all"] = auprc([(x["score"], x["active"] and x["chosen_ok"]) for x in evald if not x["hard"]])
        best["auprc_hard"] = auprc([(x["score"], x["active"] and x["chosen_ok"]) for x in evald])
        report[fam] = best
        print(f"{fam:>16}: recall {best['recall']:.3f} @ thr {best['threshold']} "
              f"(false sessions {best['false_sessions']}/48, AUPRC all {best['auprc_all']:.3f}, hard {best['auprc_hard']:.4f})", flush=True)

    (ROOT / "results" / "qwen" / "t0-matrix.json").write_text(json.dumps(report, indent=1))
    print("saved results/qwen/t0-matrix.json", flush=True)


if __name__ == "__main__":
    main()
