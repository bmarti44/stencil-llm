#!/usr/bin/env python3
# ruff: noqa: E501
"""Publish only reconstructed check40c outcomes under the repository lock."""

import fcntl
import hashlib
import json
import shutil
import sys
from contextlib import nullcontext
from pathlib import Path

ROOT = Path("/home/bmarti44/stencil-llm")
sys.path.insert(0, str(ROOT / "scripts"))


def main(locked=False):
    import focus_check40c as c
    import torch

    out = c.OUT
    with nullcontext() if locked else (ROOT / ".review.lock").open("a") as lock:
        if not locked:
            fcntl.flock(lock, fcntl.LOCK_EX)
        c.verify_freeze()
        s = json.loads((out / "summary.json").read_text())
        audit = json.loads((out / "audit.json").read_text())
        assert audit["passed"] and s["records"] == 128
        assert (
            json.loads((out / "runtime.json").read_text())["raw_slot_verified_layers"]
            == 48
        )
        kernel = json.loads((out / "kernel.json").read_text())
        assert (
            kernel["adopted"]
            and kernel["nonzero_dispatch_verified"]
            and kernel["exact_off_next_logits"]
        )
        selected = s["selected_cell"]
        if selected:
            alpha, k = {a: (alpha, k) for a, alpha, k in c.ARMS}[selected]
            bias = torch.load(
                c.OLD / "frozen-biases.pt", weights_only=True, map_location="cpu"
            )["correct"] * (alpha / 4)
            torch.save(bias, out / "selected-bias.pt")
            c.write(
                "selected-cell.json",
                dict(
                    cell=selected,
                    alpha=alpha,
                    first_k=k,
                    prefill_biased=True,
                    layers="all 48",
                    cap=64,
                    direction="JavaScript",
                    source_bias_file=str(c.OLD / "frozen-biases.pt"),
                    source_bias_sha256=c.base.sha(c.OLD / "frozen-biases.pt"),
                    bias_float32_sha256=hashlib.sha256(
                        bias.float().numpy().tobytes()
                    ).hexdigest(),
                    saved_bias_sha256=c.base.sha(out / "selected-bias.pt"),
                    selection="first qualifying arm in prewritten order; reused exploratory 32 tasks",
                    next_screen_status="frozen configuration only; no next screen run",
                ),
            )
        first_k_success = [
            a for a, _, k in c.ARMS if k is not None and s["arms"][a]["js"] >= 20
        ]
        s["first_k_js_threshold_cells"] = first_k_success
        s["paired_first_k"] = audit["paired_first_k"]
        s["qualifying_cells"] = [
            a
            for a, _, _ in c.ARMS
            if s["arms"][a]["js"] >= 20 and s["arms"][a]["broken"] <= 2
        ]
        c.write("summary.json", s)
        names = [a for a, _, _ in c.ARMS] + [
            "alpha4_sustained_reference",
            "OFF_reference",
        ]
        text = f"**{s['reading']}**. "
        text += (
            f"Freeze **{selected}** for the next screen.\n\n"
            if selected
            else "No cell meets both fixed bars.\n\n"
        )
        text += "| Cell | Valid JS | Valid Python | Broken | Coarse task pass | Truncated | => replies (valid JS / coarse pass) |\n|---|---:|---:|---:|---:|---:|---:|\n"
        for a in names:
            v = s["arms"][a]
            text += f"| {a} | {v['js']}/32 | {v['valid'].get('Python', 0)}/32 | {v['broken']}/32 | {v['task_check']}/32 | {v['truncated']} | {v['arrow_function_replies']} ({v['arrow_valid_js']} / {v['arrow_coarse_pass']}) |\n"
        text += "\nBreakage by task family (same denominators in every cell):\n\n| Cell | screen_0: ((a+b)*(c-d)) | screen_1: ((a*b)+(c*d)) | screen_2: ((a-b)-(c+d)) |\n|---|---:|---:|---:|\n"
        for a in names:
            v = s["arms"][a]["breakage_by_family"]
            text += (
                "| "
                + a
                + " | "
                + " | ".join(
                    f"{v[f]['broken']}/{v[f]['n']}"
                    for f in ("screen_0", "screen_1", "screen_2")
                )
                + " |\n"
            )
        text += "\nOpening-token and fence counts (literal decoded strings; labels do not determine parser identity):\n\n"
        for a in names:
            v = s["arms"][a]
            text += f"- {a}: first token {json.dumps(v['first_tokens'])}; first three {json.dumps(v['first_three_tokens'])}; fence {json.dumps(v['fence_labels'])}.\n"
        text += "\nPaired first-k comparisons with recorded alpha-4 sustained:\n\n"
        for a, p in audit["paired_first_k"].items():
            text += f"- {a}: first-k token IDs identical {p['first_k_identical_to_recorded_sustained']}/32; broken→unbroken {p['broken_to_unbroken']}, unbroken→broken {p['unbroken_to_broken']}; valid JS→valid Python {p['js_to_python']}.\n"
        text += "\n"
        if first_k_success:
            text += (
                "The fixed early-token JS criterion is met by "
                + ", ".join(first_k_success)
                + ". "
            )
            text += "Language selection survives turning off the direct bias after those first tokens; the paired breakage counts above measure whether sustained bias adds syntax failures. "
        else:
            text += "Neither first-k-only cell reaches 20/32 valid JS, so the fixed early-decision reading is not triggered. "
        text += (
            "The dose curve is clean at alpha 2 and 3: zero broken replies in every "
            "task family, with alpha 3 reaching 32/32 JS. Both cutoff arms still "
            "fail the <=2/32 breakage bar. First-3 fixes two broken -> replies by "
            "switching them to Python lambdas, and also switches one valid JS arrow "
            "to Python; all four Dart-style invalid replies persist. First-8 retains "
            "all six original breaks. Thus early tokens suffice for the observed "
            "JS rate, but the evidence does not support assigning all syntax failure "
            "to sustained late bias. Alpha 2 is frozen by the prewritten first-qualifying "
            "arm order; alpha 3's better descriptive JS count is also reported. "
        )
        text += "Biased prefill and earlier biased KV remain in both cutoff arms; this is not a decode-only causal isolation. This exploratory synthetic task reuse does not test persistence, SWITCH/CLEAR, other skills, benchmark transfer or fresh-task reliability.\n\n"
        text += "The inherited coarse checker remains unchanged and can reject valid arrow assignments. Arrow counts denote replies containing =>; the separate -> counts in summary.json are literal substring counts and can include Python return annotations. Both parser outcomes, flags, first-token IDs, fence labels and forward schedules are retained per reply.\n\n"
        text += f"128 new generations, {s['generated_tokens']} generated tokens; 64 recorded references copied without regeneration. Allocation **{s['gpu_seconds']:.2f} s = {s['gpu_seconds'] / 60:.2f} GPU-min**, including load ({json.loads((out / 'runtime.json').read_text())['load_seconds']:.2f} s), kernel checks and cleanup; cap 1800 s, overrun {s['cap_overrun_seconds']:.2f} s. Peak allocated {s['peak_allocated_gib']:.2f} GiB. CPU reconstruction passes; raw-logit slot equality verified on all 48 layers; grouped_mm dispatch and exact OFF verified. No fitting, training, sealed reads, signals, background launch or push.\n"
        reading = (out / "prewritten-reading.md").read_text()
        assert reading.count("\nPENDING.\n") == 1
        (out / "README.md").write_text(reading.replace("\nPENDING.\n", "\n" + text))
        for source, name in [
            ("/tmp/check40c-run.log", "run.log"),
            ("/tmp/audit_check40c.py", "audit.py"),
            ("/tmp/report_check40c.py", "report.py"),
            ("/tmp/focus_check40c.py", "executed-source.py.txt"),
            ("/tmp/check40c-reference-audit.json", "reference-cpu-audit.json"),
        ]:
            shutil.copy2(source, out / name)
        print(
            json.dumps(
                dict(
                    reading=s["reading"],
                    selected_cell=selected,
                    first_k_js_threshold_cells=first_k_success,
                )
            )
        )


if __name__ == "__main__":
    main()
