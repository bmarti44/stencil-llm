# ruff: noqa: E501
"""Gate summary for the candidate-A screen (registration §7): paired counts, exact
McNemar p, conservative paired intervals, per-lifecycle and changing-rule tables, the
five count gates and the verdict string.  Reads ``results/a-screen/runs/{off,sft,cf}.jsonl``.

Usage: ``uv run python scripts/a_screen_summary.py --runs results/a-screen/runs --out results/a-screen/RESULTS-TABLES.md``
"""

from __future__ import annotations

import argparse
import json
from math import comb
from pathlib import Path

ARMS = ("off", "sft", "cf")


def load(path: Path) -> dict[str, dict]:
    """Astra F12: keep BOTH requests per session, reject duplicates and mixed identities,
    and recompute the session outcome from the stored suite results."""
    per: dict[tuple[str, int], dict] = {}
    identities = set()
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        key = (r["session"], r["request"])
        if key in per:
            raise SystemExit(f"{path.name}: duplicate record for {key}")
        per[key] = r
        identities.add(json.dumps(r.get("identity", {}), sort_keys=True))
    if len(identities) > 1:
        raise SystemExit(
            f"{path.name}: records from {len(identities)} different identities"
        )
    out: dict[str, dict] = {}
    for (session, request), r in per.items():
        if request != 2:
            continue
        first = per.get((session, 1))
        if first is None:
            raise SystemExit(f"{path.name}: {session} has request 2 but no request 1")
        s1, s2 = first["scores"], r["scores"]
        rec = dict(r)
        rec["requests"] = [first, r]
        rec["J"] = bool(s1["all"] and s2["all"])
        rec["function_only"] = bool(s1["function_only"] and s2["function_only"])
        if rec["J"] != r["J"] or rec["function_only"] != r["function_only"]:
            raise SystemExit(
                f"{path.name}: {session} stored outcome disagrees with its suites"
            )
        out[session] = rec
    return out


def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact McNemar p on discordant counts (b wins, c losses)."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(comb(n, i) for i in range(k + 1)) / 2**n
    return min(1.0, 2 * tail)


def clopper_pearson(k: int, n: int, alpha: float) -> tuple[float, float]:
    """Exact binomial interval by bisection (no scipy)."""

    def cdf(x: int, p: float) -> float:
        return sum(comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(x + 1))

    def solve(f, lo, hi):
        for _ in range(60):
            mid = (lo + hi) / 2
            if f(mid):
                lo = mid
            else:
                hi = mid
        return lo

    lower = 0.0 if k == 0 else solve(lambda p: 1 - cdf(k - 1, p) < alpha / 2, 0.0, 1.0)
    upper = 1.0 if k == n else solve(lambda p: cdf(k, p) > alpha / 2, 0.0, 1.0)
    return lower, upper


def paired(a: dict[str, dict], b: dict[str, dict], key: str, ids: list[str]) -> dict:
    """Contrast a - b on binary ``key`` over sessions ``ids``: wins = a=1,b=0."""
    w = sum(1 for s in ids if a[s][key] and not b[s][key])
    l_ = sum(1 for s in ids if b[s][key] and not a[s][key])
    t = len(ids) - w - l_
    n = len(ids)
    # Astra F11: the registration's union bound uses two 97.5% component intervals
    wl, wu = clopper_pearson(w, n, 0.025)
    ll, lu = clopper_pearson(l_, n, 0.025)
    return {
        "n": n,
        "wins": w,
        "losses": l_,
        "ties": t,
        "net": w - l_,
        "p_mcnemar": mcnemar_exact(w, l_),
        "rate_a": sum(a[s][key] for s in ids) / n,
        "rate_b": sum(b[s][key] for s in ids) / n,
        "diff": (w - l_) / n,
        "ci95_union": (wl - lu, wu - ll),
    }


def fmt(c: dict) -> str:
    lo, hi = c["ci95_union"]
    return (
        f"{c['wins']}/{c['losses']}/{c['ties']} | net {c['net']:+d} | "
        f"{c['rate_a']:.3f} vs {c['rate_b']:.3f} | diff {c['diff']:+.3f} [{lo:+.3f}, {hi:+.3f}] | p={c['p_mcnemar']:.3f}"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", default="results/a-screen/runs")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    runs = {arm: load(Path(a.runs) / f"{arm}.jsonl") for arm in ARMS}
    ids = sorted(set.intersection(*(set(r) for r in runs.values())))
    manifest = json.loads(
        (
            Path(__file__).resolve().parents[1] / "results/a-screen/manifest.json"
        ).read_text()
    )
    expected = sorted(r["session"] for r in manifest["sessions"])
    missing = sorted(set(expected) - set(ids))
    lines = [f"# Candidate-A screen: gate tables (N = {len(ids)} complete sessions)\n"]
    lines.append(
        "| arm | J | function-only | truncated | deadline | not applied | mean s/request |"
    )
    lines.append("|---|---|---|---|---|---|---|")
    for arm in ARMS:
        recs = [runs[arm][s] for s in ids]
        both = [q for r in recs for q in r["requests"]]
        lines.append(
            f"| {arm} | {sum(r['J'] for r in recs)}/{len(ids)} | {sum(r['function_only'] for r in recs)}/{len(ids)} | "
            f"{sum(q['truncated'] for q in both)} | {sum(q['timed_out'] for q in both)} | "
            f"{sum(q['terminal_reason'] not in ('applied',) for q in both)} | {sum(q['seconds'] for q in both) / len(both):.1f} |"
        )
    cf, sft, off = runs["cf"], runs["sft"], runs["off"]
    changing = [s for s in ids if cf[s]["lifecycle"] != "stable"]
    lines.append(
        "\n## Contrasts (wins/losses/ties, net, rates, diff with conservative 95% union-bound interval, two-sided exact McNemar)\n"
    )
    lines.append("| contrast | outcome | subset | result |")
    lines.append("|---|---|---|---|")
    gates: dict[str, bool] = {}
    for name, x, y in (
        ("cf - off", cf, off),
        ("cf - sft", cf, sft),
        ("sft - off", sft, off),
    ):
        for key in ("J", "function_only"):
            c = paired(x, y, key, ids)
            lines.append(f"| {name} | {key} | all | {fmt(c)} |")
            if name == "cf - off" and key == "J":
                gates["1: net J vs off >= 5"] = c["net"] >= 5
            if name == "cf - sft" and key == "J":
                gates["2: net J vs sft >= 3"] = c["net"] >= 3
            if name == "cf - off" and key == "function_only":
                gates["3a: no net function-only decline vs off"] = c["net"] >= 0
            if name == "cf - sft" and key == "function_only":
                gates["3b: no net function-only decline vs sft"] = c["net"] >= 0
        c = paired(x, y, "J", changing)
        lines.append(f"| {name} | J | changing-rule ({len(changing)}) | {fmt(c)} |")
        if name == "cf - off":
            gates["4a: positive net J in changing sessions vs off"] = c["net"] > 0
        if name == "cf - sft":
            gates["4b: positive net J in changing sessions vs sft"] = c["net"] > 0
        for lc in ("stable", "replacement", "scope", "reinstatement"):
            sub = [s for s in ids if cf[s]["lifecycle"] == lc]
            if not sub:
                continue
            c = paired(x, y, "J", sub)
            lines.append(f"| {name} | J | {lc} ({len(sub)}) | {fmt(c)} |")
            if name in ("cf - off", "cf - sft") and lc != "stable":
                gates[f"5: net J >= 0 in {lc} ({name})"] = c["net"] >= 0
    lines.append("\n## Per target family (J per arm)\n")
    lines.append("| target | off | sft | cf | n |")
    lines.append("|---|---|---|---|---|")
    for fam in sorted({cf[s]["target_family"] for s in ids}):
        sub = [s for s in ids if cf[s]["target_family"] == fam]
        lines.append(
            f"| {fam} | {sum(off[s]['J'] for s in sub)} | {sum(sft[s]['J'] for s in sub)} | {sum(cf[s]['J'] for s in sub)} | {len(sub)} |"
        )
    lines.append("\n## Gate (registration §7; count rules decide)\n")
    for g, ok in gates.items():
        lines.append(f"- {g}: {'PASS' if ok else 'FAIL'}")
    verdict = "GATE PASSED" if gates and all(gates.values()) else "GATE FAILED"
    if missing:
        verdict = (
            f"INCOMPLETE ({len(ids)}/{len(expected)} manifest sessions complete in all "
            f"three arms; missing {', '.join(missing)}); provisional: {verdict}"
        )
    lines.append(
        f"\n**Verdict: {verdict}** (a passed gate authorises only the CONFIRM registration; no efficacy claim)."
    )
    text = "\n".join(lines) + "\n"
    print(text)
    if a.out:
        Path(a.out).write_text(text)


if __name__ == "__main__":
    main()
