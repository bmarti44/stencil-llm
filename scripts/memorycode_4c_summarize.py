"""Exp 4C analysis: the single summary of the package-path evaluation.

Implements REGISTRATION-4C.md mechanically: record validity against the qualification
fingerprint and the frozen item manifest; completeness (every frozen pair terminal and
scored); budget accounting incl. interrupted attempts against 3 t_max N; the paired-t
primary on ``fraction_required`` (Hoeffding fallback at zero variance) with the
percentile bootstrap and sign test as companions; strict compliance with McNemar and the
conservative paired interval; the output-failure guard (paired t on H = F_on − F_off,
Clopper-Pearson fallback at zero variance, McNemar p) with the registered U_H ≤ 0.05
gate; the exhaustive readings table; descriptive subset breakdowns.

Writes <records dir>/summary-4c.json. The pure functions ``analyze`` and ``reading_4c``
are what the tests exercise.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
OUT = ROOT / "results" / "memorycode-long"

_spec = importlib.util.spec_from_file_location(
    "memorycode_package_run", ROOT / "scripts" / "memorycode_package_run.py"
)
runner = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(runner)
screen = runner.screen

MARGIN = 0.05  # registered noninferiority margin on the failure-rate difference
FAILURE_KEYS = ("invalid", "truncated", "degenerate", "timed_out")


# ------------------------------------------------------------------ statistics
def paired_t(diffs: list[float]) -> dict:
    """Two-sided paired t-test of E[D] = 0 with the matching 95% interval; the
    registered Hoeffding fallback when the sample SD is zero."""
    from scipy.stats import t as tdist

    n = len(diffs)
    mean = sum(diffs) / n
    if n < 2:
        return {
            "n": n,
            "mean": mean,
            "sd": None,
            "lower": None,
            "upper": None,
            "p": None,
        }
    var = sum((d - mean) ** 2 for d in diffs) / (n - 1)
    sd = math.sqrt(var)
    if sd == 0.0:
        half = math.sqrt(2 * math.log(40) / n)
        return {
            "n": n,
            "mean": mean,
            "sd": 0.0,
            "lower": max(mean - half, -1.0),
            "upper": min(mean + half, 1.0),
            "p": min(1.0, 2 * math.exp(-n * mean * mean / 2)),
            "method": "hoeffding-fallback (s_D = 0)",
        }
    se = sd / math.sqrt(n)
    q = tdist.ppf(0.975, n - 1)
    stat = mean / se
    p = 2 * tdist.sf(abs(stat), n - 1)
    return {
        "n": n,
        "mean": mean,
        "sd": sd,
        "se": se,
        "t": stat,
        "lower": mean - q * se,
        "upper": mean + q * se,
        "p": float(p),
        "method": "paired t",
    }


def _valid_reason(rec: dict, expect: dict, items_sha: str) -> str | None:
    m = rec.get("manifest") or {}
    if not m:
        return "no manifest"
    if not runner.fingerprint_matches(m, expect):
        return "fingerprint mismatch"
    if m.get("items_sha256") != items_sha:
        return "items manifest mismatch"
    if not all(a in rec.get("arms", {}) for a in ("base", "focus")):
        return "missing arm"
    tokens = []
    for arm in ("base", "focus"):
        gens = rec["arms"][arm].get("generations") or []
        if len(gens) != 1:
            return f"{arm}: {len(gens)} generations"
        g = gens[0]
        if g.get("termination") not in ("eos", "cap", "timeout"):
            return f"{arm}: non-terminal"
        if "generated_token_ids_raw" not in g or "generated_token_ids" not in g:
            return f"{arm}: raw ids missing"
        s = g.get("scores") or {}
        if "per_family" not in s or "fraction_required" not in s:
            return f"{arm}: unscored"
        if s["fraction_required"] is None:
            return f"{arm}: inapplicable item"
        if not g.get("failures"):
            return f"{arm}: failures missing"
        tokens.append((g.get("window") or {}).get("prompt_tokens"))
    if tokens[0] != tokens[1] or tokens[0] is None:
        return "prompt token counts differ"
    return None


def _score(rec: dict, arm: str) -> float:
    g = rec["arms"][arm]["generations"][0]
    if g.get("timed_out"):
        return 0.0
    return float(g["scores"]["fraction_required"])


def _fails(rec: dict, arm: str) -> bool:
    f = rec["arms"][arm]["generations"][0]["failures"]
    return any(bool(f.get(k)) for k in FAILURE_KEYS)


def analyze(
    records: list[dict],
    frozen_ids: list[str],
    expect_manifest: dict,
    items_sha: str,
    ceiling_seconds: float | None,
    spent_seconds: float,
    marker_exists: bool = False,
) -> dict:
    """The registered analysis on in-memory records (pure; used by the tests)."""
    by_id = {}
    invalid = {}
    duplicates = []
    for rec in records:
        rid = rec["id"]
        if rid in by_id:
            duplicates.append(rid)
            continue
        why = _valid_reason(rec, expect_manifest, items_sha)
        if why:
            invalid[rid] = why
            continue
        by_id[rid] = rec
    frozen = list(frozen_ids)
    missing = [i for i in frozen if i not in by_id]
    extra = sorted(set(by_id) - set(frozen))
    complete = not missing and not invalid and not duplicates
    budget = {
        "ceiling_seconds": ceiling_seconds,
        "spent_seconds": spent_seconds,
        "marker": marker_exists,
        "exhausted": marker_exists
        or (ceiling_seconds is not None and spent_seconds > ceiling_seconds),
    }
    technical_ok = complete and not budget["exhausted"]
    ids = sorted(i for i in frozen if i in by_id)  # lexicographic (registration)
    on = [_score(by_id[i], "focus") for i in ids]
    off = [_score(by_id[i], "base") for i in ids]
    diffs = [a - b for a, b in zip(on, off)]
    fon = [_fails(by_id[i], "focus") for i in ids]
    foff = [_fails(by_id[i], "base") for i in ids]
    hs = [float(a) - float(b) for a, b in zip(fon, foff)]
    stats = {"n": len(ids)}
    if ids:
        stats["primary"] = paired_t(diffs)
        stats["primary"]["mean_off"] = sum(off) / len(off)
        stats["primary"]["mean_on"] = sum(on) / len(on)
        stats["bootstrap"] = screen._paired_mean_bootstrap(on, off)
        son = [bool(by_id[i]["arms"]["focus"]["strict"]) for i in ids]
        soff = [bool(by_id[i]["arms"]["base"]["strict"]) for i in ids]
        stats["strict"] = {
            "on": sum(son),
            "off": sum(soff),
            "mcnemar": screen._mcnemar(list(zip(son, soff))),
            "paired_interval": screen._paired_interval(list(zip(son, soff))),
        }
        guard = paired_t(hs)
        if guard.get("sd") == 0.0:
            cp = screen._paired_interval(list(zip(fon, foff)))
            guard = {
                "n": len(hs),
                "mean": sum(hs) / len(hs),
                "sd": 0.0,
                "lower": cp["lower_points"] / 100,
                "upper": cp["upper_points"] / 100,
                "p": None,
                "method": "clopper-pearson union bound (s_H = 0)",
            }
        guard["mcnemar"] = screen._mcnemar(list(zip(fon, foff)))
        guard["on_only"] = sum(1 for a, b in zip(fon, foff) if a and not b)
        guard["off_only"] = sum(1 for a, b in zip(fon, foff) if b and not a)
        guard["rate_on"] = sum(fon) / len(fon)
        guard["rate_off"] = sum(foff) / len(foff)
        guard["categories"] = {
            arm: {
                k: sum(
                    1
                    for i in ids
                    if by_id[i]["arms"][arm]["generations"][0]["failures"].get(k)
                )
                for k in FAILURE_KEYS
            }
            for arm in ("base", "focus")
        }
        guard["margin"] = MARGIN
        guard["gate_U_H_le_margin"] = guard["upper"] is not None and (
            guard["upper"] <= MARGIN
        )
        guard["equivalence_within_margin"] = (
            guard["lower"] is not None
            and guard["upper"] is not None
            and -MARGIN <= guard["lower"]
            and guard["upper"] <= MARGIN
        )
        guard["demonstrated_increase"] = (
            guard["lower"] is not None and guard["lower"] > 0
        )
        stats["failure_guard"] = guard
        subsets = {}
        for name, pred in (
            ("screen_128", lambda r: (r.get("candidate_index") or 0) < 128),
            ("reserve", lambda r: (r.get("candidate_index") or 0) >= 128),
        ):
            sub = [i for i in ids if pred(by_id[i])]
            if sub:
                subsets[name] = {
                    "n": len(sub),
                    "mean_off": sum(_score(by_id[i], "base") for i in sub) / len(sub),
                    "mean_on": sum(_score(by_id[i], "focus") for i in sub) / len(sub),
                }
        stats["subsets_descriptive"] = subsets
    status = {
        "complete": complete,
        "missing_ids": missing,
        "invalid_records": invalid,
        "duplicate_ids": duplicates,
        "extra_ids": extra,
        "budget": budget,
        "technical_ok": technical_ok,
    }
    return {"status": status, "stats": stats, "reading": reading_4c(status, stats)}


def reading_4c(status: dict, stats: dict, eligible: bool = True) -> dict:
    """REGISTRATION-4C.md readings table, applied mechanically: technical status,
    then primary efficacy, then the failure guard."""
    if not eligible:
        verdict, publish = "INELIGIBLE; efficacy NOT PROVEN", False
    elif not status["technical_ok"]:
        verdict, publish = "INCOMPLETE", False
    else:
        p = stats["primary"]
        g = stats["failure_guard"]
        if p["upper"] < 0:
            verdict, publish = "HARM", False
        elif p["lower"] <= 0:
            verdict, publish = "NOT PROVEN, FINAL", False
        elif g["upper"] > MARGIN and g["lower"] <= MARGIN:
            verdict = "POSITIVE EFFICACY / NONINFERIORITY UNRESOLVED; NOT PROVEN, FINAL"
            publish = False
        elif g["lower"] > MARGIN:
            verdict = (
                "POSITIVE EFFICACY / DEMONSTRATED EXCESS OUTPUT HARM; NOT PROVEN, FINAL"
            )
            publish = False
        else:
            verdict = (
                "STATISTICAL GATES PASSED (pending audit and release verification)"
            )
            publish = True  # HF push only after audit + clean-environment verification
    return {
        "verdict": verdict,
        "statistical_gates_passed": publish,
        "hf_release_authorized_after_audit_and_verification": publish,
        "note": (
            "PROVEN, SCOPED is declared only after the result audit and the "
            "clean-environment reproduction accept; nothing here is a claim until then."
        ),
    }


# ------------------------------------------------------------------ driver
def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--items-file", default=str(OUT / "items-4c.json"))
    parser.add_argument("--qualification", default=str(OUT / "qualification-4c.json"))
    parser.add_argument("--records", default=None, help="records directory")
    parser.add_argument("--model", default="4b")
    args = parser.parse_args(argv)
    frozen = json.loads(Path(args.items_file).read_text())
    qual = json.loads(Path(args.qualification).read_text())
    items_sha = screen._sha256(Path(args.items_file))
    split = frozen["items"][0]["split"]

    class A:
        cohort = "long"
        model = args.model
        policy = "role_evicted"
        runtime = "package"

    A.split = split
    records_dir = Path(args.records) if args.records else screen._out_dir(A)
    records = [
        json.loads(p.read_text()) for p in sorted(records_dir.glob("item-*.json"))
    ]
    expect = dict(qual["manifest"])
    expect["items_sha256"] = items_sha
    expect["budget_tokens"] = expect.get("budget_tokens") or 256
    n = frozen["n"]
    t_max = frozen["t_max_seconds"] or qual["t_max_seconds"]
    ceiling = 3 * t_max * n
    spent = screen._generation_seconds(records_dir, ["base", "focus"])
    spent += runner.interrupted_seconds(records_dir)
    out = analyze(
        records,
        [it["id"] for it in frozen["items"]],
        expect,
        items_sha,
        ceiling,
        spent,
        screen._ceiling_marker(records_dir).exists(),
    )
    out["reading"] = reading_4c(out["status"], out["stats"], eligible=qual["eligible"])
    out["registration"] = "results/memorycode-long/REGISTRATION-4C.md"
    out["items_file"] = args.items_file
    out["items_sha256"] = items_sha
    out["frozen_ids_sha256"] = frozen.get("frozen_ids_sha256")
    out["n_registered"] = n
    out["t_max_seconds"] = t_max
    out["git_sha"] = screen._git_sha()
    screen._write_atomic(records_dir / "summary-4c.json", out)
    print(json.dumps({"status": out["status"], "reading": out["reading"]}, indent=1))
    if "primary" in out["stats"]:
        p, g = out["stats"]["primary"], out["stats"]["failure_guard"]
        print(
            json.dumps(
                {
                    "n": p["n"],
                    "mean_off": p["mean_off"],
                    "mean_on": p["mean_on"],
                    "diff_points": 100 * p["mean"],
                    "ci_points": [100 * p["lower"], 100 * p["upper"]],
                    "p": p["p"],
                    "failure_diff_points": 100 * g["mean"],
                    "failure_ci_points": [100 * g["lower"], 100 * g["upper"]],
                    "strict": [
                        out["stats"]["strict"]["off"],
                        out["stats"]["strict"]["on"],
                    ],
                },
                indent=1,
            )
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
