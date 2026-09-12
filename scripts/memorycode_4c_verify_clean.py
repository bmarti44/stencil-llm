"""Exp 4C release verification, CLEAN-ENVIRONMENT half (no research-repo imports).

Run inside a fresh virtual environment with pinned dependencies and an empty
remote-code cache: loads the STAGED package through the documented public API
(``AutoModelForCausalLM.from_pretrained(dir, trust_remote_code=True)`` +
``model.new_session`` / ``add_message`` / ``generate``), replays the prospectively
fixed qualification calls (SETUP item 359-99, both flag states) from their receipts
and requires byte-identical prompts, identical prompt ids, identical effective
generation settings and identical raw outputs including EOS; also checks the
scored-id/text reconstruction. Writes the verification report; the caller enforces
the 900-second resident allowance with ``timeout``.

usage: memorycode_4c_verify_clean.py <staged_dir> <out.json> <receipt.json>...
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

SKIP_FILES = {"README.md"}
SKIP_DIRS = {"__pycache__", ".git"}


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def package_files(hub: Path) -> dict[str, str]:
    out = {}
    for p in sorted(hub.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(hub)
        if rel.name in SKIP_FILES or set(rel.parts[:-1]) & SKIP_DIRS:
            continue
        out[rel.as_posix()] = sha256_file(p)
    return out


def fingerprint(files: dict[str, str]) -> str:
    h = hashlib.sha256()
    for name in sorted(files):
        h.update(f"{name}\n{files[name]}\n".encode())
    return h.hexdigest()


def main(argv: list[str]) -> int:
    started = time.monotonic()
    staged, out_path = Path(argv[0]), Path(argv[1])
    receipts = [Path(p) for p in argv[2:]]
    forbidden = [m for m in sys.modules if m == "stencil" or m.startswith("stencil.")]
    import tokenizers
    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer

    files = package_files(staged)
    tokenizer = AutoTokenizer.from_pretrained(staged)
    model = AutoModelForCausalLM.from_pretrained(
        staged, trust_remote_code=True, dtype=torch.bfloat16, device_map="cuda"
    )
    model.eval()
    eos = model.config.eos_token_id
    eos = sorted({int(i) for i in (eos if isinstance(eos, (list, tuple)) else [eos])})
    calls = []
    for rp in receipts:
        r = json.loads(rp.read_text())
        session = model.new_session(tokenizer, stencil_focus=(r["arm"] == "focus"))
        for role, text, rendered in r["messages"]:
            session.add_message(role, text, rendered=rendered)
        prompt = session.build_prompt(
            r["request"], head=r["head"], separator=r["separator"]
        )
        prompt_ids = session.encode(prompt)
        t0 = time.monotonic()
        session.generate(
            r["request"],
            head=r["head"],
            separator=r["separator"],
            max_new_tokens=r["max_new"],
            max_time=r["deadline"],
        )
        seconds = time.monotonic() - t0
        raw = list(session.last["generated_token_ids"])
        ended = bool(raw) and raw[-1] in eos
        scored = raw[:-1] if ended else raw
        text = tokenizer.decode(scored, skip_special_tokens=True)
        calls.append(
            {
                "receipt": rp.name,
                "id": r["id"],
                "arm": r["arm"],
                "prompt_bytes_match": prompt == r["prompt"],
                "prompt_ids_match": prompt_ids == r["prompt_ids"],
                "eos_match": eos == r["eos_token_ids"],
                "settings_match": r["max_new"] == 512 and r["deadline"] == 300.0,
                "raw_match": raw == r["raw_ids"],
                "scored_match": scored == r["scored_ids"],
                "text_match": text == r["text"],
                "seconds": seconds,
                "reference_seconds": r["seconds"],
            }
        )
    keys = (
        "prompt_bytes_match",
        "prompt_ids_match",
        "eos_match",
        "settings_match",
        "raw_match",
        "scored_match",
        "text_match",
    )
    passed = bool(calls) and all(all(c[k] for k in keys) for c in calls)
    passed = passed and not forbidden
    report = {
        "staged_dir": str(staged),
        "package_files": files,
        "package_sha256": fingerprint(files),
        "eos_token_ids": eos,
        "environment": {
            "python": sys.version.split()[0],
            "torch": torch.__version__,
            "transformers": transformers.__version__,
            "tokenizers": tokenizers.__version__,
            "cuda": torch.version.cuda,
            "gpu_name": torch.cuda.get_device_name(0),
            "attn_implementation": getattr(model.config, "_attn_implementation", None),
            "executable": sys.executable,
            "sys_path_has_research_src": any("stencil-llm/src" in p for p in sys.path),
            "research_modules_imported": forbidden,
        },
        "calls": calls,
        "passed": passed,
        "resident_seconds": time.monotonic() - started,
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    out_path.write_text(json.dumps(report, indent=1))
    print(
        json.dumps(
            {k: report[k] for k in ("passed", "resident_seconds", "package_sha256")}
        )
    )
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
