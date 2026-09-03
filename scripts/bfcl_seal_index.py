#!/usr/bin/env python3
"""One-time authorized BFCL cohort byte-offset index builder (CPU only)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/bench/bfcl_v3_mt"
CATEGORIES = ("base", "missing_params", "missing_functions", "long_context")
PIN_NAME = "ShishirPatil/gorilla BFCL V3 multi-turn"


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _atomic_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=1) + "\n")
    temporary.replace(path)


def main() -> None:
    cohorts = json.loads((DATA / "cohorts.json").read_text())
    wanted = set(cohorts["dev"]) | set(cohorts["sealed"])
    manifest_path = ROOT / "data/bench/pins-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    pinned = manifest["pins"][PIN_NAME]
    registered_hashes = pinned["files_sha256"]
    records: dict[str, dict] = {case_id: {} for case_id in wanted}
    source_hashes = {}

    # This is the sole authorized population read. Each mixed source is opened once.
    for kind in ("case", "answer"):
        plural = "cases" if kind == "case" else "answers"
        for category in CATEGORIES:
            path = DATA / f"{plural}_{category}.jsonl"
            relative = str(path.relative_to(ROOT))
            raw = path.read_bytes()
            digest = _sha256(raw)
            if registered_hashes.get(relative) != digest:
                raise RuntimeError(f"frozen BFCL source hash mismatch: {relative}")
            source_hashes[relative] = digest
            offset = 0
            for line in raw.splitlines(keepends=True):
                row = json.loads(line)
                case_id = str(row["id"])
                if case_id in wanted:
                    if kind in records[case_id]:
                        raise RuntimeError(f"duplicate {kind} row: {case_id}")
                    records[case_id][kind] = {
                        "file": relative,
                        "offset": offset,
                        "length": len(line),
                        "category": category,
                    }
                offset += len(line)

    incomplete = {case_id: sorted(row) for case_id, row in records.items()
                  if set(row) != {"case", "answer"}}
    if incomplete:
        raise RuntimeError(f"incomplete cohort offsets: {incomplete}")
    index = {
        "schema": 1,
        "cohorts_sha256": _sha256((DATA / "cohorts.json").read_bytes()),
        "cohorts": {"dev": cohorts["dev"], "sealed": cohorts["sealed"]},
        "source_files_sha256": dict(sorted(source_hashes.items())),
        "records": {case_id: records[case_id]
                    for case_id in [*cohorts["dev"], *cohorts["sealed"]]},
    }
    index_path = DATA / "offsets.json"
    _atomic_json(index_path, index)
    pinned["offsets_sha256"] = _sha256(index_path.read_bytes())
    _atomic_json(manifest_path, manifest)


if __name__ == "__main__":
    main()
