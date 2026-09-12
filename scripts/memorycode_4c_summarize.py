"""Exp 4C analysis: the single summary of the package-path evaluation.

Implements REGISTRATION-4C.md mechanically (Astra implementation review applied):
the freeze chain (registered hashes, qualification digest, timing-derived N) is
re-verified; every record is validated for CONSISTENCY, not just presence (finite
bounded scores, finite non-negative timing, boolean failure categories, raw-to-scored
EOS transformation, termination/timeout/cap agreement, prompt hash/count/allocation,
item identity against the frozen manifest, per-arm fingerprints, strict-score
consistency) and re-scored from its saved text with the frozen checker; extra,
duplicate, unknown-arm, malformed or misnamed files block confirmation; budget
compliance is established from the attempt log and process receipts (generation ≤
3 t_max N, resident overhead ≤ 2,700 s, qualification ≤ 3,600 s; unbounded accounting
is INCOMPLETE); the paired-t primary on ``fraction_required`` takes the Hoeffding
fallback on EXACTLY constant differences (detected by equality, before any variance
arithmetic) and uses ``math.fsum``; the output-failure guard likewise; every positive
decision requires finite interval endpoints.

Finalization: without ``--terminal`` only operational completeness and cost are
written (progress-4c.json, no efficacy); ``--terminal`` writes summary-4c.json ONCE.
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
items4c = runner.items4c

MARGIN = 0.05  # registered noninferiority margin on the failure-rate difference
FAILURE_KEYS = ("invalid", "truncated", "degenerate", "timed_out")
ARMS = ("base", "focus")
ITEM_KEYS = ("id", "session", "queries", "history_regex", "candidate_index")


def _finite(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


# ------------------------------------------------------------------ statistics
def paired_t(diffs: list[float]) -> dict:
    """Two-sided paired t-test of E[D] = 0 with the matching 95% interval; the
    registered Hoeffding fallback when the differences are EXACTLY constant (checked
    by equality to the first value before any variance arithmetic, finding 8)."""
    from scipy.stats import t as tdist

    n = len(diffs)
    if n == 0 or not all(_finite(d) for d in diffs):
        return {
            "n": n,
            "mean": None,
            "sd": None,
            "lower": None,
            "upper": None,
            "p": None,
            "method": "undefined",
        }
    mean = math.fsum(diffs) / n
    if n < 2:
        return {
            "n": n,
            "mean": mean,
            "sd": None,
            "lower": None,
            "upper": None,
            "p": None,
            "method": "undefined",
        }
    if all(d == diffs[0] for d in diffs):
        mean = diffs[0]
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
    var = math.fsum((d - mean) ** 2 for d in diffs) / (n - 1)
    sd = math.sqrt(var)
    se = sd / math.sqrt(n)
    q = float(tdist.ppf(0.975, n - 1))
    stat = mean / se
    p = 2 * tdist.sf(abs(stat), n - 1)
    return {
        "n": n,
        "mean": mean,
        "sd": sd,
        "se": se,
        "t": stat,
        "t_quantile": q,
        "lower": mean - q * se,
        "upper": mean + q * se,
        "p": float(p),
        "method": "paired t",
    }


# ------------------------------------------------------------------ validity
def _gen_reason(g: dict, arm: str, expect: dict, max_new: int) -> str | None:
    if not isinstance(g, dict):
        return f"{arm}: generation not a dict"
    term = g.get("termination")
    if term not in ("eos", "cap", "timeout"):
        return f"{arm}: non-terminal"
    raw, ids = g.get("generated_token_ids_raw"), g.get("generated_token_ids")
    if not isinstance(raw, list) or not isinstance(ids, list):
        return f"{arm}: raw ids missing"
    if not all(isinstance(t, int) and not isinstance(t, bool) for t in raw + ids):
        return f"{arm}: non-integer ids"
    eos = expect.get("eos_token_ids") or []
    if g.get("eos_token_ids") != eos:
        return f"{arm}: eos set differs from the frozen effective set"
    ended = bool(raw) and raw[-1] in eos
    if g.get("ended_by_eos") is not ended:
        return f"{arm}: ended_by_eos inconsistent"
    if ids != (raw[:-1] if ended else raw):
        return f"{arm}: scored ids are not raw minus a terminal EOS"
    if len(raw) > max_new:
        return f"{arm}: more than max_new raw ids"
    truncated = (not ended) and len(raw) >= max_new
    if g.get("truncated") is not truncated:
        return f"{arm}: truncated flag inconsistent"
    for k in ("timed_out",):
        if not isinstance(g.get(k), bool):
            return f"{arm}: {k} not boolean"
    secs = g.get("seconds")
    if not _finite(secs) or secs < 0:
        return f"{arm}: seconds not finite non-negative"
    deadline = expect["decoding"]["deadline"]
    expected_timeout = secs > deadline or (not ended and not truncated)
    if (
        g["timed_out"] is not expected_timeout
        or (term == "timeout") is not expected_timeout
    ):
        return f"{arm}: timeout classification inconsistent"
    if term == "cap" and not truncated or term == "eos" and not ended:
        return f"{arm}: termination inconsistent"
    if g.get("n_generated") != len(ids) or g.get("n_generated_raw") != len(raw):
        return f"{arm}: token counts inconsistent"
    f = g.get("failures")
    if not isinstance(f, dict) or any(
        not isinstance(f.get(k), bool) for k in FAILURE_KEYS
    ):
        return f"{arm}: failure categories missing or non-boolean"
    if f["truncated"] is not truncated or f["timed_out"] is not g["timed_out"]:
        return f"{arm}: failure flags disagree with termination"
    s = g.get("scores")
    if not isinstance(s, dict) or "per_family" not in s or "fraction_required" not in s:
        return f"{arm}: unscored"
    fr = s["fraction_required"]
    if fr is None:
        return f"{arm}: inapplicable item"
    if not _finite(fr) or not 0.0 <= fr <= 1.0:
        return f"{arm}: fraction_required not in [0, 1]"
    if not isinstance(s.get("strict"), bool):
        return f"{arm}: strict not boolean"
    if g["timed_out"] and (fr != 0.0 or s["strict"]):
        return f"{arm}: timeout must score zero"
    if not isinstance(g.get("prompt"), str):
        return f"{arm}: prompt text missing"
    w = g.get("window") or {}
    if not isinstance(w.get("prompt_tokens"), int):
        return f"{arm}: prompt token count missing"
    if g.get("prompt_ids_count") != w["prompt_tokens"]:
        return f"{arm}: prompt id count differs from window"
    if w["prompt_tokens"] + max_new > 4096:
        return f"{arm}: allocation exceeds 4096"
    import hashlib

    if g.get("prompt_sha256") != hashlib.sha256(g["prompt"].encode()).hexdigest():
        return f"{arm}: prompt hash mismatch"
    return None


def _with_raw(g: dict, data: dict, arm: str, rec: dict, raw_loader) -> dict | str:
    """Prompt text/hashes/count and the window live in the linked raw-output file
    (the runner persists them there before scoring); merge them into a copy of the
    generation after cross-checking the link (attempt id, arm, item, raw ids)."""
    g = dict(g)
    if "prompt" in g and "window" in g:
        return g
    if raw_loader is None:
        return f"{arm}: prompt text missing"
    raw = raw_loader(data.get("raw_file"))
    if not isinstance(raw, dict):
        return f"{arm}: raw output file missing"
    if raw.get("attempt_id") != data.get("attempt_id") or raw.get("arm") != arm:
        return f"{arm}: raw file does not match the arm's attempt"
    if raw.get("id") != rec.get("id"):
        return f"{arm}: raw file belongs to another item"
    rg = raw.get("generation") or {}
    if rg.get("generated_token_ids_raw") != g.get("generated_token_ids_raw"):
        return f"{arm}: raw ids differ between record and raw file"
    if raw.get("manifest") != data.get("manifest"):
        return f"{arm}: raw file manifest differs from the arm manifest"
    for k in ("prompt", "prompt_sha256", "prompt_ids_count", "window"):
        g[k] = raw.get(k)
    return g


def _valid_reason(
    rec: dict,
    expect: dict,
    item: dict | None,
    rescore=None,
    decode=None,
    raw_loader=None,
) -> str | None:
    if not isinstance(rec, dict):
        return "malformed record"
    if item is None:
        return "not in the frozen manifest"
    for k in ITEM_KEYS:
        if rec.get(k) != item.get(k):
            return f"item identity differs on {k}"
    arms = rec.get("arms")
    if not isinstance(arms, dict):
        return "arms missing"
    if set(arms) != set(ARMS):
        return "unknown or missing arm"
    max_new = expect["decoding"]["max_new"]
    tokens = []
    for arm in ARMS:
        data = arms[arm]
        m = data.get("manifest") or {}
        if not m:
            return f"{arm}: no manifest"
        if not runner.fingerprint_matches(m, expect):
            return f"{arm}: fingerprint mismatch"
        gens = data.get("generations") or []
        if len(gens) != 1:
            return f"{arm}: {len(gens)} generations"
        g = _with_raw(gens[0], data, arm, rec, raw_loader)
        if isinstance(g, str):
            return g
        why = _gen_reason(g, arm, expect, max_new)
        if why:
            return why
        if data.get("strict") is not g["scores"]["strict"]:
            return f"{arm}: arm strict differs from scores"
        if decode is not None and decode(g["generated_token_ids"]) != g["text"]:
            return f"{arm}: text is not the decoded scored ids"
        if rescore is not None:
            scores, failures = rescore(item, g)
            if scores != g["scores"] or failures != g["failures"]:
                return f"{arm}: stored scores/failures differ from the frozen checker"
        if arm == "focus" and not isinstance(data.get("reminder_sources"), dict):
            return "focus: reminder provenance missing"
        tokens.append(g["window"]["prompt_tokens"])
    if tokens[0] != tokens[1]:
        return "prompt token counts differ"
    return None


def _score(rec: dict, arm: str) -> float:
    g = rec["arms"][arm]["generations"][0]
    return 0.0 if g["timed_out"] else float(g["scores"]["fraction_required"])


def _fails(rec: dict, arm: str) -> bool:
    f = rec["arms"][arm]["generations"][0]["failures"]
    return any(f[k] for k in FAILURE_KEYS)


def analyze(
    records: list,
    frozen_items: list[dict],
    expect_manifest: dict,
    ceiling_seconds: float | None,
    accounting: dict,
    marker_exists: bool = False,
    rescore=None,
    decode=None,
    raw_loader=None,
) -> dict:
    """The registered analysis on in-memory records (pure; used by the tests).
    ``records`` may contain (name, record) pairs or bare records; ``accounting``
    carries generation/overhead/qualification seconds and an ``unbounded`` flag."""
    items = {it["id"]: it for it in frozen_items}
    by_id: dict[str, dict] = {}
    invalid: dict[str, str] = {}
    duplicates = []
    for i, entry in enumerate(records):
        name, rec = entry if isinstance(entry, tuple) else (None, entry)
        rid = rec.get("id") if isinstance(rec, dict) else None
        label = rid if isinstance(rid, str) else (name or f"record-{i}")
        if not isinstance(rec, dict) or not isinstance(rid, str):
            invalid[label] = "malformed record"
            continue
        if name is not None and name != f"item-{rid}.json":
            invalid[label] = f"filename {name} does not match id"
            continue
        if rid in by_id or rid in duplicates:
            duplicates.append(rid)
            continue
        why = _valid_reason(
            rec, expect_manifest, items.get(rid), rescore, decode, raw_loader
        )
        if why:
            invalid[label] = why
            continue
        by_id[rid] = rec
    frozen = [it["id"] for it in frozen_items]
    missing = [i for i in frozen if i not in by_id]
    extra = sorted(set(by_id) - set(frozen))
    complete = not missing and not invalid and not duplicates and not extra
    gen = accounting.get("generation_seconds")
    budget = {
        "ceiling_seconds": ceiling_seconds,
        "generation_seconds": gen,
        "overhead_seconds": accounting.get("overhead_seconds"),
        "overhead_allowance": runner.OVERHEAD_ALLOWANCE,
        "qualification_seconds": accounting.get("qualification_seconds"),
        "qualification_allowance": runner.QUALIFICATION_ALLOWANCE,
        "unbounded": bool(accounting.get("unbounded")),
        "marker": marker_exists,
    }
    budget["exhausted"] = (
        marker_exists
        or budget["unbounded"]
        or not _finite(gen)
        or (ceiling_seconds is not None and gen > ceiling_seconds)
        or not _finite(budget["overhead_seconds"])
        or budget["overhead_seconds"] > runner.OVERHEAD_ALLOWANCE
        or not _finite(budget["qualification_seconds"])
        or budget["qualification_seconds"] > runner.QUALIFICATION_ALLOWANCE
    )
    ids = sorted(i for i in frozen if i in by_id)  # lexicographic (registration)
    on = [_score(by_id[i], "focus") for i in ids]
    off = [_score(by_id[i], "base") for i in ids]
    diffs = [a - b for a, b in zip(on, off)]
    fon = [_fails(by_id[i], "focus") for i in ids]
    foff = [_fails(by_id[i], "base") for i in ids]
    hs = [float(a) - float(b) for a, b in zip(fon, foff)]
    stats: dict = {"n": len(ids)}
    finite = False
    if ids:
        stats["primary"] = paired_t(diffs)
        stats["primary"]["mean_off"] = math.fsum(off) / len(off)
        stats["primary"]["mean_on"] = math.fsum(on) / len(on)
        stats["bootstrap"] = screen._paired_mean_bootstrap(on, off)
        son = [by_id[i]["arms"]["focus"]["strict"] for i in ids]
        soff = [by_id[i]["arms"]["base"]["strict"] for i in ids]
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
                "mean": math.fsum(hs) / len(hs),
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
                    if by_id[i]["arms"][arm]["generations"][0]["failures"][k]
                )
                for k in FAILURE_KEYS
            }
            for arm in ARMS
        }
        guard["margin"] = MARGIN
        finite = all(
            _finite(x)
            for x in (
                stats["primary"]["lower"],
                stats["primary"]["upper"],
                guard["lower"],
                guard["upper"],
            )
        )
        guard["gate_U_H_le_margin"] = finite and guard["upper"] <= MARGIN
        guard["equivalence_within_margin"] = (
            finite and -MARGIN <= guard["lower"] and guard["upper"] <= MARGIN
        )
        guard["demonstrated_increase"] = finite and guard["lower"] > 0
        stats["failure_guard"] = guard
        subsets = {}
        for name, pred in (
            ("screen_128", lambda it: it["candidate_index"] < 128),
            ("reserve", lambda it: it["candidate_index"] >= 128),
        ):
            sub = [i for i in ids if pred(items[i])]
            if sub:
                subsets[name] = {
                    "n": len(sub),
                    "mean_off": math.fsum(_score(by_id[i], "base") for i in sub)
                    / len(sub),
                    "mean_on": math.fsum(_score(by_id[i], "focus") for i in sub)
                    / len(sub),
                }
        stats["subsets_descriptive"] = subsets
    status = {
        "complete": complete,
        "n_valid": len(by_id),
        "missing_ids": missing,
        "invalid_records": invalid,
        "duplicate_ids": duplicates,
        "extra_ids": extra,
        "budget": budget,
        "finite_statistics": finite,
        "technical_ok": complete and not budget["exhausted"] and finite,
    }
    return {"status": status, "stats": stats, "reading": reading_4c(status, stats)}


def reading_4c(status: dict, stats: dict, eligible: bool = True) -> dict:
    """REGISTRATION-4C.md readings table, applied mechanically: technical status,
    then primary efficacy, then the failure guard. Non-finite statistics never reach
    a positive decision (finding 7)."""
    if not eligible:
        verdict, publish = "INELIGIBLE; efficacy NOT PROVEN", False
    elif not status["technical_ok"] or not status.get("finite_statistics"):
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
        elif g["upper"] <= MARGIN and p["lower"] > 0:
            verdict = (
                "STATISTICAL GATES PASSED (pending audit and release verification)"
            )
            publish = True  # HF push only after audit + clean-environment verification
        else:  # pragma: no cover - exhaustive above
            verdict, publish = "INCOMPLETE", False
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
def load_records(records_dir: Path) -> list:
    out = []
    for p in sorted(records_dir.glob("item-*.json")):
        try:
            out.append((p.name, json.loads(p.read_text())))
        except (json.JSONDecodeError, UnicodeDecodeError):
            out.append((p.name, None))
    return out


def analysis_environment() -> dict:
    import numpy
    import scipy

    return {
        "python": sys.version.split()[0],
        "numpy": numpy.__version__,
        "scipy": scipy.__version__,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--items-file", default=str(OUT / "items-4c.json"))
    parser.add_argument("--qualification", default=str(OUT / "qualification-4c.json"))
    parser.add_argument("--records", default=None, help="records directory")
    parser.add_argument(
        "--hub", default=str(ROOT / "deploy/stencil_focus/build/hub-4b")
    )
    parser.add_argument(
        "--terminal", action="store_true", help="write summary-4c.json once"
    )
    args = parser.parse_args(argv)
    from stencil import memorycode as mc

    frozen = json.loads(Path(args.items_file).read_text())
    qual = json.loads(Path(args.qualification).read_text())
    problems = items4c.verify_frozen(
        frozen, qual, screen._sha256(Path(args.qualification))
    )
    items_sha = screen._sha256(Path(args.items_file))

    class A:
        cohort, model, policy, runtime = (
            "long",
            qual["manifest"]["model"],
            "role_evicted",
            "package",
        )
        split = frozen["items"][0]["split"]

    records_dir = Path(args.records) if args.records else screen._out_dir(A)
    expect = dict(qual["manifest"], items_sha256=items_sha)
    if expect.get("checker_sha256") != runner.checker_hashes():
        problems.append("checker files changed since qualification")
    ceiling = 3 * frozen["t_max_seconds"] * frozen["n"]
    acct = runner.attempt_accounting(records_dir, expect["decoding"]["deadline"])
    resident = runner.resident_seconds(records_dir)
    qual_resident = runner.resident_seconds(OUT / "qualification-4c")
    accounting = {
        "generation_seconds": acct["generation_seconds"],
        "attempts": acct,
        "resident": resident,
        "overhead_seconds": resident["overhead_seconds"],
        "qualification_seconds": qual_resident["resident_seconds"],
        "unbounded": acct["unbounded"]
        or resident["unbounded"]
        or qual_resident["unbounded"],
    }
    compute_score = mc.vendored_checker()
    from tokenizers import Tokenizer

    tok = Tokenizer.from_file(str(Path(args.hub) / "tokenizer.json"))

    def rescore(item, g):
        q = item["queries"][0]
        scores = mc.score_generation(
            g["text"],
            item["history_regex"],
            compute_score,
            required=item["required"][q],
            structure=item["structure"][q],
        )
        if g["timed_out"]:
            scores["strict"] = False
            if scores.get("fraction_required") is not None:
                scores["fraction_required"] = 0.0
        failures = mc.output_failures(
            g["text"], g["generated_token_ids"], g["truncated"], g["timed_out"]
        )
        return scores, failures

    def decode(ids):
        return tok.decode(ids, skip_special_tokens=True)

    def raw_loader(name):
        p = records_dir / "raw" / str(name)
        try:
            return json.loads(p.read_text()) if p.exists() else None
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None

    out = analyze(
        load_records(records_dir),
        frozen["items"],
        expect,
        ceiling,
        accounting,
        screen._ceiling_marker(records_dir).exists(),
        rescore=rescore,
        decode=decode,
        raw_loader=raw_loader,
    )
    if problems:
        out["status"]["chain_problems"] = problems
        out["status"]["technical_ok"] = False
    out["reading"] = reading_4c(
        out["status"], out["stats"], eligible=qual["eligible"] and not problems
    )
    out.update(
        {
            "registration": "results/memorycode-long/REGISTRATION-4C.md",
            "items_file": args.items_file,
            "items_sha256": items_sha,
            "frozen_ids_sha256": frozen.get("frozen_ids_sha256"),
            "qualification_sha256": screen._sha256(Path(args.qualification)),
            "n_registered": frozen["n"],
            "t_max_seconds": frozen["t_max_seconds"],
            "git_sha": screen._git_sha(),
            "analysis_environment": analysis_environment(),
        }
    )
    if not args.terminal:
        progress = {k: out[k] for k in ("registration", "n_registered")}
        progress["status"] = {
            k: v for k, v in out["status"].items() if k != "finite_statistics"
        }
        screen._write_atomic(records_dir / "progress-4c.json", progress)
        print(json.dumps(progress["status"], indent=1))
        return 0
    target = records_dir / "summary-4c.json"
    if target.exists():
        raise SystemExit(f"{target} exists; the summary is computed once")
    screen._write_atomic(target, out)
    print(json.dumps({"status": out["status"], "reading": out["reading"]}, indent=1))
    if "primary" in out["stats"]:
        p, g = out["stats"]["primary"], out["stats"]["failure_guard"]
        print(
            json.dumps(
                {
                    "n": p["n"],
                    "mean_off": p["mean_off"],
                    "mean_on": p["mean_on"],
                    "diff_points": 100 * p["mean"] if _finite(p["mean"]) else None,
                    "ci_points": [100 * p["lower"], 100 * p["upper"]]
                    if _finite(p["lower"])
                    else None,
                    "p": p["p"],
                    "failure_diff_points": 100 * g["mean"]
                    if _finite(g["mean"])
                    else None,
                    "failure_ci_points": [100 * g["lower"], 100 * g["upper"]]
                    if _finite(g["lower"])
                    else None,
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
