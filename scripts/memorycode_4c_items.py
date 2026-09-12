"""Exp 4C candidate order and frozen item manifest (REGISTRATION-4C.md).

Candidate order: reconstruct ``long_items`` from the vendored MemoryCode revision with
the research tokenizer, apply the seed-1 dialogue shuffle of ``split_long``, drop the
first 16 SETUP-LONG dialogues; the remaining 196 dialogues (one item each) are the
ordered candidates, whose first 128 must reproduce the original SCREEN-LONG definitions
in ``items.json`` exactly. ``--freeze N`` writes ``items-4c.json`` with the first N
candidates (N from the timing-only rule; never from any outcome).

Writes results/memorycode-long/items-4c-candidates.json (always) and items-4c.json
(``--freeze``).
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
    keys = ("dialogue", "session", "queries", "required", "structure", "history_regex")
    for mine, theirs in zip(ordered[:128], screen_items):
        for k in keys:
            if mine[k] != theirs[k]:
                raise SystemExit(f"candidate {mine['id']} differs from SCREEN on {k}")
    for i, item in enumerate(ordered):
        item["candidate_index"] = i
        item["source"] = "screen_long" if i < 128 else "reserve"
        item["split"] = "screen_long_4c"
    return {
        "registration": "results/memorycode-long/REGISTRATION-4C.md",
        "vendor_sha": VENDOR_SHA,
        "items_json_sha256": screen._sha256(OUT / "items.json"),
        "n_long_items": len(items),
        "n_candidates": len(ordered),
        "candidate_ids_sha256": ids_sha256([it["id"] for it in ordered]),
        "window_tokens": mc.WINDOW,
        "reminder_budget_tokens": mc.BUDGET,
        "items": ordered,
    }


def sample_size(t_max: float, n_candidates: int = 196) -> int:
    """N = min(196, floor(28,800 / (3 t_max))); INELIGIBLE below 128."""
    return min(n_candidates, int(28_800 // (3 * t_max)))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--freeze", type=int, default=0, help="N to freeze")
    parser.add_argument("--t-max", type=float, default=None, help="pilot t_max (s)")
    parser.add_argument(
        "--qualification", default=None, help="qualification.json the t_max came from"
    )
    args = parser.parse_args(argv)
    payload = candidates()
    screen = _screen()
    screen._write_atomic(OUT / "items-4c-candidates.json", payload)
    print(json.dumps({k: v for k, v in payload.items() if k != "items"}, indent=1))
    if args.freeze or args.t_max:
        n = args.freeze or sample_size(args.t_max, payload["n_candidates"])
        if args.t_max and args.freeze and args.freeze != sample_size(args.t_max):
            raise SystemExit("--freeze disagrees with the timing rule")
        if n < 128:
            raise SystemExit(f"INELIGIBLE-BUDGET: N={n} < 128")
        chosen = payload["items"][:n]
        frozen = {
            **{k: v for k, v in payload.items() if k != "items"},
            "n": n,
            "t_max_seconds": args.t_max,
            "qualification": args.qualification,
            "rule": "N = min(196, floor(28800 / (3 * t_max)))",
            "frozen_ids_sha256": ids_sha256([it["id"] for it in chosen]),
            "items": chosen,
        }
        if (OUT / "items-4c.json").exists():
            raise SystemExit("items-4c.json already frozen; never re-freeze")
        screen._write_atomic(OUT / "items-4c.json", frozen)
        print(f"frozen N={n} sha={frozen['frozen_ids_sha256']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
