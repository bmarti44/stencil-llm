"""Exp 4C candidate order and frozen item manifest (REGISTRATION-4C.md).

Candidate order: reconstruct ``long_items`` from the vendored MemoryCode revision with
the research tokenizer, apply the seed-1 dialogue shuffle of ``split_long``, drop the
first 16 SETUP-LONG dialogues; the remaining 196 dialogues (one item each) are the
ordered candidates, whose first 128 must reproduce the original SCREEN-LONG definitions
in ``items.json`` exactly, and whose hashes must equal the REGISTERED constants.

Freezing (review finding 5) consumes the completed qualification report ONLY:
``--qualification results/memorycode-long/qualification-4c.json`` must be eligible,
carry the eight prescribed timing calls, and t_max / N are recomputed from it; the
qualification digest and package fingerprint are stored in ``items-4c.json``, which is
written once. ``verify_frozen`` rechecks the whole chain for the runner and summary.

Writes results/memorycode-long/items-4c-candidates.json (``--candidates``) and
items-4c.json (``--qualification``).
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
OUT = ROOT / "results" / "memorycode-long"
VENDOR_SHA = "1ab87e119b2f9a498de8075219e1c07f6041b394"
# registered constants (REGISTRATION-4C.md, "Candidate order and sample size")
ITEMS_JSON_SHA256 = "affe6877f059e5f58466023fe70c45cefeadca4b98d1a036832901d14073ce1a"
CANDIDATE_IDS_SHA256 = (
    "3125634e658bf35fc20e8555199abb5cc8f30ada4c14f328caba08fa7e43ca28"
)
N_CANDIDATES = 196
N_MIN = 128
EVALUATION_SECONDS = 28_800
TIMING_IDS = ["359-99", "352-99", "351-99", "302-49"]
TIMING_CALLS = [(iid, arm) for iid in TIMING_IDS for arm in ("base", "focus")]
RULE = "N = min(196, floor(28800 / (3 * t_max)))"


def _screen():
    spec = importlib.util.spec_from_file_location(
        "memorycode_screen", ROOT / "scripts" / "memorycode_screen.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def ids_sha256(ids: list[str]) -> str:
    return hashlib.sha256(("\n".join(ids) + "\n").encode()).hexdigest()


def candidates() -> dict:
    from stencil import memorycode as mc

    screen = _screen()
    items_json_sha = screen._sha256(OUT / "items.json")
    if items_json_sha != ITEMS_JSON_SHA256:
        raise SystemExit(f"items.json sha {items_json_sha} != registered")
    tokenizer = screen._tokenizer()
    items = mc.long_items(tokenizer)
    split = mc.split_long(items, n_setup=16, n_screen=len(items))
    ordered = split["screen_long"]  # every dialogue after the 16 SETUP ones, in order
    for item in ordered:
        item["id"] = f"{item['dialogue']}-{item['session']}"
    original = json.loads((OUT / "items.json").read_text())
    screen_items = [it for it in original["items"] if it["split"] == "screen_long"]
    setup_ids = {it["id"] for it in original["items"] if it["split"] == "setup_long"}
    assert not setup_ids & {it["id"] for it in ordered}, "SETUP dialogue in candidates"
    assert len(screen_items) == 128
    if len(ordered) != N_CANDIDATES:
        raise SystemExit(f"{len(ordered)} candidates != registered {N_CANDIDATES}")
    keys = ("dialogue", "session", "queries", "required", "structure", "history_regex")
    for mine, theirs in zip(ordered[:128], screen_items):
        for k in keys:
            if mine[k] != theirs[k]:
                raise SystemExit(f"candidate {mine['id']} differs from SCREEN on {k}")
    for i, item in enumerate(ordered):
        item["candidate_index"] = i
        item["source"] = "screen_long" if i < 128 else "reserve"
        item["split"] = "screen_long_4c"
    sha = ids_sha256([it["id"] for it in ordered])
    if sha != CANDIDATE_IDS_SHA256:
        raise SystemExit(f"candidate ids sha {sha} != registered")
    return {
        "registration": "results/memorycode-long/REGISTRATION-4C.md",
        "vendor_sha": VENDOR_SHA,
        "items_json_sha256": items_json_sha,
        "n_long_items": len(items),
        "n_candidates": len(ordered),
        "candidate_ids_sha256": sha,
        "window_tokens": mc.WINDOW,
        "reminder_budget_tokens": mc.BUDGET,
        "items": ordered,
    }


def sample_size(t_max: float, n_candidates: int = N_CANDIDATES) -> int:
    """N = min(196, floor(28,800 / (3 t_max))); INELIGIBLE below 128."""
    return min(n_candidates, int(EVALUATION_SECONDS // (3 * t_max)))


def timing_from_qualification(qual: dict) -> tuple[float, list[str]]:
    """t_max recomputed from the eight prescribed timing calls; problems listed."""
    problems = []
    calls = qual.get("timing_calls") or []
    identity = [(c.get("id"), c.get("arm")) for c in calls]
    if identity != TIMING_CALLS:
        problems.append(f"timing calls {identity} != prescribed {TIMING_CALLS}")
    secs = []
    for c in calls:
        s = c.get("seconds")
        if not isinstance(s, (int, float)) or not (s > 0) or s != s:
            problems.append(f"timing call {c.get('id')} {c.get('arm')}: bad seconds")
        else:
            secs.append(float(s))
    t_max = max(secs) if secs else float("nan")
    if secs and abs(t_max - float(qual.get("t_max_seconds", -1))) > 1e-9:
        problems.append("reported t_max differs from the timing calls")
    return t_max, problems


def verify_frozen(frozen: dict, qual: dict, qual_sha256: str) -> list[str]:
    """Every link of the freeze chain (finding 5); an empty list means valid."""
    problems = []
    if frozen.get("items_json_sha256") != ITEMS_JSON_SHA256:
        problems.append("items.json sha differs from the registered constant")
    if frozen.get("candidate_ids_sha256") != CANDIDATE_IDS_SHA256:
        problems.append("candidate ids sha differs from the registered constant")
    if frozen.get("qualification_sha256") != qual_sha256:
        problems.append("qualification digest differs from the frozen manifest")
    if not qual.get("eligible"):
        problems.append("qualification not eligible")
    if not qual.get("passed"):
        problems.append("qualification not passed")
    m = qual.get("manifest") or {}
    if frozen.get("package_sha256") != m.get("package_sha256") or not m.get(
        "package_sha256"
    ):
        problems.append("package fingerprint differs from the qualification")
    t_max, tp = timing_from_qualification(qual)
    problems += tp
    if not tp:
        if abs(float(frozen.get("t_max_seconds", -1)) - t_max) > 1e-9:
            problems.append("frozen t_max differs from the qualification timing calls")
        n = sample_size(t_max)
        if frozen.get("n") != n:
            problems.append(f"frozen n {frozen.get('n')} != rule {n}")
        if n < N_MIN:
            problems.append("N below 128")
    items = frozen.get("items") or []
    if len(items) != frozen.get("n"):
        problems.append("len(items) != n")
    ids = [it.get("id") for it in items]
    if frozen.get("frozen_ids_sha256") != ids_sha256(ids):
        problems.append("frozen ids sha differs from the items")
    cand_path = OUT / "items-4c-candidates.json"
    if cand_path.exists():
        cand = json.loads(cand_path.read_text())
        if cand.get("candidate_ids_sha256") != CANDIDATE_IDS_SHA256:
            problems.append("candidate file sha differs from the registered constant")
        prefix = cand["items"][: len(items)]
        if ids_sha256([it["id"] for it in cand["items"]]) != CANDIDATE_IDS_SHA256:
            problems.append("candidate file ids do not reproduce the registered sha")
        keys = (
            "id",
            "dialogue",
            "session",
            "queries",
            "required",
            "structure",
            "history_regex",
            "candidate_index",
            "source",
            "split",
        )
        if len(prefix) != len(items) or any(
            a.get(k) != b.get(k) for a, b in zip(prefix, items) for k in keys
        ):
            problems.append("frozen items are not the exact candidate prefix")
    else:
        problems.append("items-4c-candidates.json missing")
    return problems


def freeze(qual_path: Path, payload: dict, screen) -> dict:
    qual = json.loads(qual_path.read_text())
    qual_sha = screen._sha256(qual_path)
    t_max, problems = timing_from_qualification(qual)
    if problems:
        raise SystemExit("qualification unusable: " + "; ".join(problems))
    if not qual.get("passed") or not qual.get("eligible"):
        raise SystemExit("qualification not passed/eligible; no freeze")
    n = sample_size(t_max, payload["n_candidates"])
    if n < N_MIN:
        raise SystemExit(f"INELIGIBLE-BUDGET: N={n} < 128")
    chosen = payload["items"][:n]
    frozen = {
        **{k: v for k, v in payload.items() if k != "items"},
        "n": n,
        "t_max_seconds": t_max,
        "qualification": str(qual_path),
        "qualification_sha256": qual_sha,
        "package_sha256": qual["manifest"]["package_sha256"],
        "rule": RULE,
        "ceiling_seconds": 3 * t_max * n,
        "frozen_ids_sha256": ids_sha256([it["id"] for it in chosen]),
        "items": chosen,
    }
    problems = verify_frozen(frozen, qual, qual_sha)
    if problems:
        raise SystemExit("freeze self-check failed: " + "; ".join(problems))
    return frozen


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--candidates", action="store_true", help="rewrite the candidate file"
    )
    parser.add_argument(
        "--qualification", default=None, help="freeze N from this report"
    )
    args = parser.parse_args(argv)
    payload = candidates()
    screen = _screen()
    cand_path = OUT / "items-4c-candidates.json"
    if args.candidates or not cand_path.exists():
        screen._write_atomic(cand_path, payload)
    elif (
        json.loads(cand_path.read_text())["candidate_ids_sha256"]
        != payload["candidate_ids_sha256"]
    ):
        raise SystemExit("existing candidate file disagrees with the reconstruction")
    print(json.dumps({k: v for k, v in payload.items() if k != "items"}, indent=1))
    if args.qualification:
        if (OUT / "items-4c.json").exists():
            raise SystemExit("items-4c.json already frozen; never re-freeze")
        frozen = freeze(Path(args.qualification), payload, screen)
        screen._write_atomic(OUT / "items-4c.json", frozen)
        print(
            f"frozen N={frozen['n']} t_max={frozen['t_max_seconds']} "
            f"sha={frozen['frozen_ids_sha256']}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
