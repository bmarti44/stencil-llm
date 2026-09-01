# ruff: noqa
"""Secondary, policy-level own-history Multi-IF run after replay gate pass."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401

OPENER = "<|im_start|>assistant\n<think>\n\n</think>\n\n"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--deadline", type=float, default=300.0)
    parser.add_argument("--out", default="e2-multiif-own-history")
    return parser.parse_args()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic_json(path, value):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=1))
    tmp.rename(path)


def main():
    args = parse_args()
    import torch
    from tokenizers import Tokenizer

    from stencil.bench import MAX_NEW
    from stencil.ctrb import HazardGate
    from stencil.e2 import user_turn_span_records
    from stencil.e2_multiif import (
        base_branch,
        is_diagnostic_key,
        paired_endpoint,
        policy_branch,
        score_turn,
        turn_doc,
    )
    from stencil.e2_policy import generate_e2_policy
    from stencil.qwen3 import Qwen3
    from stencil.wave import WaveController

    replay_summary_path = ROOT / "results" / "qwen" / "e2-multiif-replay" / "summary.json"
    replay_summary = json.loads(replay_summary_path.read_text())
    if not replay_summary["primary"]["gate_pass"]:
        raise RuntimeError("own-history run requires a passing replayed-history gate")
    freeze_path = ROOT / "results" / "qwen" / "e2-freeze.json"
    freeze = json.loads(freeze_path.read_text())
    if freeze.get("own_history_runner_sha256") != sha(Path(__file__)):
        raise RuntimeError("post-freeze own-history runner drift")
    gate_report = json.loads((ROOT / freeze["gate_report"]).read_text())
    fitted = gate_report["gate"]
    gate = HazardGate(
        tuple(fitted["mean"]),
        tuple(fitted["scale"]),
        tuple(fitted["weights"]),
        float(fitted["bias"]),
    )
    data_path = ROOT / "data" / "bench" / "multiif_en.jsonl"
    base_dir = ROOT / "results" / "qwen" / "b4-multiif-base"
    model_path = ROOT / "models" / "qwen3-1.7b.pt"
    controller_path = ROOT / "results" / "qwen" / "b3-ce-s0.pt"
    rows = [json.loads(line) for line in data_path.read_text().splitlines()]
    base_records = [
        json.loads((base_dir / f"conv-{i:03d}.json").read_text()) for i in range(909)
    ]
    outdir = ROOT / "results" / "qwen" / args.out
    outdir.mkdir(parents=True, exist_ok=True)
    meta = {
        "schema": 1,
        "replay_summary_sha256": sha(replay_summary_path),
        "freeze_sha256": sha(freeze_path),
        "runner_sha256": sha(Path(__file__)),
        "policy_sha256": sha(ROOT / "src" / "stencil" / "e2_policy.py"),
        "conversations": 909,
        "deadline": args.deadline,
        "scope": "secondary_confounded_own_history",
    }
    meta_path = outdir / "meta.json"
    if meta_path.exists():
        if json.loads(meta_path.read_text()) != meta:
            raise RuntimeError("own-history resume provenance mismatch")
    else:
        atomic_json(meta_path, meta)

    tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
    model = Qwen3()
    model.load_state_dict(torch.load(model_path, map_location="cpu"), strict=True)
    model = model.to(torch.bfloat16).cuda().eval()
    ctrl = WaveController(beta_max=1.0).cuda()
    ctrl.load_state_dict(torch.load(controller_path, map_location="cpu"))
    ctrl = ctrl.eval()

    for ci, (row, base_record) in enumerate(zip(rows, base_records, strict=True)):
        record_path = outdir / f"conv-{ci:03d}.json"
        if record_path.exists():
            continue
        present = [turn for turn in (1, 2, 3) if row[f"turn_{turn}_prompt"]]
        history = ""
        turns = {}
        for turn in present:
            prompt, _, _ = turn_doc(row, turn)
            history_now = history + f"<|im_start|>user\n{prompt}<|im_end|>\n"
            base = base_branch(base_record, turn)
            if turn == 1:
                branch = dict(base)
            else:
                context = history_now + OPENER
                spans = user_turn_span_records(tok, context)
                result = generate_e2_policy(
                    model, tok, context, ctrl, spans,
                    mode="ctrb", gate=gate, threshold=float(freeze["threshold"]),
                    dose=float(freeze["dose"]), max_new=MAX_NEW,
                    deadline_s=args.deadline, raw_context=True)
                branch = policy_branch(result, score_turn(row, turn, result.text))
            turns[str(turn)] = {"base": base, "ctrb": branch}
            history = history_now + f"<|im_start|>assistant\n{branch['response']}<|im_end|>\n"
        atomic_json(
            record_path,
            {
                "ci": ci,
                "key": row["key"],
                "diagnostic": is_diagnostic_key(row["key"]),
                "turns": turns,
            },
        )
        print(f"own-history conversation {ci + 1}/909", flush=True)

    records = [
        json.loads((outdir / f"conv-{i:03d}.json").read_text()) for i in range(909)
    ]
    partitions = {}
    for diagnostic in (False, True):
        selected = [record for record in records if record["diagnostic"] is diagnostic]
        inst = {str(turn): [] for turn in (1, 2, 3)}
        prompt = {str(turn): [] for turn in (1, 2, 3)}
        inst["pooled"], prompt["pooled"] = [], []
        controls = {"base_truncations": 0, "arm_truncations": 0,
                    "base_timeouts": 0, "arm_timeouts": 0,
                    "base_tokens": 0, "arm_tokens": 0, "turns": 0}
        for record in selected:
            for turn, bundle in record["turns"].items():
                base, arm = bundle["base"], bundle["ctrb"]
                pairs = list(zip(base["scores"]["inst_level_strict_acc"],
                                 arm["scores"]["inst_level_strict_acc"], strict=True))
                inst[turn].extend(pairs); inst["pooled"].extend(pairs)
                pp = (base["scores"]["prompt_level_strict_acc"],
                      arm["scores"]["prompt_level_strict_acc"])
                prompt[turn].append(pp); prompt["pooled"].append(pp)
                controls["base_truncations"] += int(base["truncated"])
                controls["arm_truncations"] += int(arm["truncated"])
                controls["base_timeouts"] += int(base["timed_out"])
                controls["arm_timeouts"] += int(arm["timed_out"])
                controls["base_tokens"] += base["n_generated"]
                controls["arm_tokens"] += arm["n_generated"]
                controls["turns"] += 1
        partitions["diagnostic" if diagnostic else "primary"] = {
            "conversations": len(selected),
            "inst_level": {key: paired_endpoint(value) for key, value in inst.items() if value},
            "strict_prompt": {key: paired_endpoint(value) for key, value in prompt.items() if value},
            "controls": controls,
        }
    summary = {**meta, "partitions": partitions}
    atomic_json(outdir / "summary.json", summary)
    print(json.dumps(summary, indent=1), flush=True)


if __name__ == "__main__":
    main()
