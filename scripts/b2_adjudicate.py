# ruff: noqa
"""B2 BINDING do-no-harm adjudicator (v4.1; sol checkpoint-iii FINDING-3).

Frozen construction: for EACH wave seed (b3-ce-s0, b3-ce-s1) and EACH
suite (MMLU-Redux ok-5330 margin 0.5pt, GSM8K-1319 margin 1.0pt):
- the wave arm's record directory must be COMPLETE (every item) with
  meta.ctrl_sha256 equal to the REGISTERED selected-checkpoint hash;
- discordances are computed from PER-ITEM records (never aggregates);
- the registered Tango 95% upper bound must be STRICTLY below the
  margin. BOTH seeds must pass BOTH suites for the binding PASS.
Fail-closed: any missing record, provenance mismatch, or Tango
non-convergence = FAIL. This script only reads records; the arms are
produced by scripts/b2_mmlu.py / b2_gsm8k.py with CTRL set to the
registered checkpoint paths (same runners as the recorded base arms).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil.stats import tango_upper_bound

CTRL_SHA = {
    "b3-ce-s0": "0e2574ffd431406f7ffba15e9940e42d7f141c27566d6b02110b38acebb6c524",
    "b3-ce-s1": "e028b63f95623fe9d35b4f89eed07ab51effdcde6cc380370d4ac95dc4bcd631",
}
SUITES = {
    "mmlu": {"n": 5330, "margin": 0.005, "base_dir": "b2-mmlu-base", "wave_dir": "b2-mmlu-{seed}"},
    "gsm8k": {"n": 1319, "margin": 0.01, "base_dir": "b2-gsm8k-base", "wave_dir": "b2-gsm8k-{seed}"},
}


def load_items(dirname, n):
    d = ROOT / "results" / "qwen" / dirname
    if not d.exists():
        raise SystemExit(f"FAIL (fail-closed): missing record dir {dirname}")
    items = {}
    for p in d.glob("item-*.json"):
        r = json.loads(p.read_text())
        items[r["i"] if "i" in r else r["idx"]] = bool(r["right"])
    if len(items) != n:
        raise SystemExit(f"FAIL (fail-closed): {dirname} has {len(items)}/{n} records")
    return items


def main():
    verdicts = {}
    for seed, want_sha in CTRL_SHA.items():
        for suite, cfg in SUITES.items():
            wdir = cfg["wave_dir"].format(seed=seed)
            meta_p = ROOT / "results" / "qwen" / wdir / "meta.json"
            if not meta_p.exists():
                raise SystemExit(f"FAIL (fail-closed): missing meta for {wdir}")
            meta = json.loads(meta_p.read_text())
            if meta["ctrl_sha256"] != want_sha:
                raise SystemExit(f"FAIL (fail-closed): {wdir} ctrl hash {meta['ctrl_sha256'][:12]} != registered")
            base = load_items(cfg["base_dir"], cfg["n"])
            wave = load_items(wdir, cfg["n"])
            if set(base) != set(wave):
                raise SystemExit(f"FAIL (fail-closed): item-set mismatch {wdir}")
            n10 = sum(1 for i in base if base[i] and not wave[i])
            n01 = sum(1 for i in base if not base[i] and wave[i])
            u = tango_upper_bound(n10, n01, cfg["n"])  # raises on non-convergence
            verdicts[f"{seed}/{suite}"] = {
                "n10": n10, "n01": n01, "N": cfg["n"],
                "acc_base": round(sum(base.values()) / cfg["n"], 6),
                "acc_wave": round(sum(wave.values()) / cfg["n"], 6),
                "tango_upper_95": round(u, 6), "margin": cfg["margin"],
                "pass": bool(u < cfg["margin"]),
            }
    binding = all(v["pass"] for v in verdicts.values())
    out = {"verdicts": verdicts, "BINDING_DO_NO_HARM_PASS": binding}
    print(json.dumps(out, indent=1))
    (ROOT / "results" / "qwen" / "b2-binding-adjudication.json").write_text(json.dumps(out, indent=1))
    if not binding:
        sys.exit(1)


if __name__ == "__main__":
    main()
