"""Exp 4C: recompute the focus arms' reminder provenance from unchanged outputs (CPU).

Result-audit finding 1 (results/reviews/2026-09-12-exp4c-result-audit-astra.md): the
runner recorded ``reminder_sources`` against the shortened focus-window boundary while
the package selects evicted sentences against the BASE-window boundary, so the recorded
spans did not reproduce the reminders. This script rebuilds every focus session through
the package's own ``Session`` (tokenizer only, no model), asserts the rebuilt prompt is
byte-identical to the stored raw prompt and the rebuilt reminder equals the recorded
one, recomputes the provenance with the corrected ``reminder_sources`` and writes it
into
the terminal record with a disclosure note. Raw outputs, scores and statistics are not
touched. Writes <records>/reprovenance-4c.json.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "deploy" / "stencil_focus"))
OUT = ROOT / "results" / "memorycode-long"

_spec = importlib.util.spec_from_file_location(
    "memorycode_package_run", ROOT / "scripts" / "memorycode_package_run.py"
)
runner = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(runner)
screen = runner.screen


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--records", default=str(OUT / "screen_long_4c-4b-package-role_evicted")
    )
    parser.add_argument(
        "--hub", default=str(ROOT / "deploy/stencil_focus/build/hub-4b")
    )
    args = parser.parse_args(argv)
    from stencil_focus.focus_session import Session
    from transformers import AutoTokenizer

    from stencil import memorycode as mc

    tok = AutoTokenizer.from_pretrained(args.hub)
    records_dir = Path(args.records)
    report = {"records": {}, "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    for path in sorted(records_dir.glob("item-*.json")):
        rec = json.loads(path.read_text())
        arm = rec["arms"]["focus"]
        raw = json.loads((records_dir / "raw" / arm["raw_file"]).read_text())
        dialogue = mc.load_dialogue(int(rec["id"].split("-")[0]))
        head, sep, request = mc.long_request(dialogue, rec["queries"][0])
        session = Session(tok, focus=True)
        for role, text, rendered in mc.focus_session_messages(dialogue, rec["session"]):
            session.add_message(role, text, rendered=rendered)
        prompt = session.build_prompt(request, head=head, separator=sep)
        built = dict(session.last)
        if prompt != raw["prompt"]:
            raise SystemExit(f"{rec['id']}: rebuilt prompt differs from the raw prompt")
        if built["reminder"] != arm["reminder"]:
            raise SystemExit(f"{rec['id']}: rebuilt reminder differs from the record")
        if built["kept_sentences"] != arm["kept_sentences"]:
            raise SystemExit(f"{rec['id']}: kept_sentences differ")
        old = arm.get("reminder_sources") or {}
        new = runner.reminder_sources(session, built, head, sep, request)
        new["recomputed"] = {
            "reason": "result-audit finding 1: boundary taken from the focus window",
            "previous_eviction_boundary_char": old.get("eviction_boundary_char"),
            "previous_evicted_spans": old.get("evicted_spans"),
            "utc": report["utc"],
        }
        arm["reminder_sources"] = new
        arm["selected_sentences"] = built["evicted_sentences"]
        screen._write_atomic(path, rec)
        report["records"][rec["id"]] = {
            "boundary_before": old.get("eviction_boundary_char"),
            "boundary_after": new["eviction_boundary_char"],
            "kept": len(new["kept_spans"]),
        }
        print(
            rec["id"],
            old.get("eviction_boundary_char"),
            "->",
            new["eviction_boundary_char"],
            flush=True,
        )
    screen._write_atomic(records_dir / "reprovenance-4c.json", report)
    print(f"recomputed {len(report['records'])} focus arms")
    return 0


if __name__ == "__main__":
    sys.exit(main())
