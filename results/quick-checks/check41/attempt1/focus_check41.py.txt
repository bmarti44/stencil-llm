#!/usr/bin/env python3
"""Unregistered check 41: dense Qwen3-4B programming-language neuron scaling."""

# ruff: noqa: E501
from __future__ import annotations

import argparse
import hashlib
import importlib.machinery
import importlib.util
import inspect
import json
import math
import subprocess
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/quick-checks/check41"
MODEL = ROOT / "models/qwen3-4b-hf"
SEED = 41041
GPU_SECONDS = 7200
CAP = 256
LANGS = ("Python", "JavaScript")
ARMS = ("correct", "swapped", "shuffled", "OFF", "text-cue")
STEPS = ("SET", "NEUTRAL", "HOLD", "SWITCH", "BACK", "CLEAR")
TARGETS = dict(
    SET="JavaScript",
    HOLD="JavaScript",
    SWITCH="Python",
    BACK="JavaScript",
    CLEAR=None,
    NEUTRAL=None,
)
KS = (200, 500, 1000)
loader = importlib.machinery.SourceFileLoader(
    "check40_pinned", str(OUT / "check40-source.py.txt")
)
spec = importlib.util.spec_from_loader(loader.name, loader)
base = importlib.util.module_from_spec(spec)
loader.exec_module(base)
# Snapshot's file location differs; only pure tasks/checkers/utilities are reused.
base.ROOT = ROOT
sha, write_json, score = base.sha, base.write_json, base.score
BudgetStop = base.BudgetStop


class NeuronHooks:
    """Pre-down-projection hook consumes the actual SiLU(gate)*up product."""

    def __init__(self, projections):
        self.projections = projections
        self.scale = None
        self.capture = False
        self.prefill = False
        self.counts = [0] * len(projections)
        self.freqs = None
        self.handles = [
            p.register_forward_pre_hook(self.hook(i)) for i, p in enumerate(projections)
        ]

    def reset_capture(self):
        import torch

        p = self.projections[0]
        self.freqs = torch.zeros(
            len(self.projections),
            p.in_features,
            dtype=torch.int64,
            device=p.weight.device,
        )
        self.counts = [0] * len(self.projections)

    def hook(self, layer):
        def apply(module, inputs):
            x = inputs[0]
            if self.capture:
                assert not self.prefill and x.shape[:2] == (1, 1)
                self.freqs[layer].add_((x.detach() > 0).sum(dim=(0, 1)))
                self.counts[layer] += 1
            if self.scale is None:
                return None
            if self.prefill:
                # Only final prompt position predicts the first generated token.
                y = x.clone()
                y[:, -1:, :] *= self.scale[layer]
            else:
                y = x * self.scale[layer]
            return (y,) + inputs[1:]

        return apply

    def close(self):
        for handle in self.handles:
            handle.remove()


def select_neurons(frequencies, ks=KS):
    import torch

    f = frequencies.double()
    assert (
        f.shape[0] == 2
        and torch.isfinite(f).all()
        and (f >= 0).all()
        and (f <= 1).all()
    )
    p = f / f.sum(0, keepdim=True).clamp_min(1e-30)
    entropy = -(p * p.clamp_min(1e-30).log()).sum(0) / math.log(2)
    entropy[f.sum(0) == 0] = 1
    # LAPE-style low-entropy specificity weighted by signed frequency difference.
    specificity = (f - f.flip(0)) * (1 - entropy).clamp_min(0)
    sets = {}
    width = f.shape[2]
    for k in ks:
        chosen = [
            torch.argsort(s.flatten(), descending=True, stable=True)[:k].tolist()
            for s in specificity
        ]
        layers = [
            {
                lang: sum(n // width == layer for n in chosen[j])
                for j, lang in enumerate(LANGS)
            }
            for layer in range(f.shape[1])
        ]
        overlap = len(set(chosen[0]) & set(chosen[1]))
        sets[str(k)] = dict(
            k=k,
            flat_indices=dict(zip(LANGS, chosen, strict=True)),
            layer_counts=layers,
            overlap_count=overlap,
            overlap_fraction=overlap / k,
            nonpositive_selected={
                lang: sum(float(specificity[j].flatten()[n]) <= 0 for n in chosen[j])
                for j, lang in enumerate(LANGS)
            },
        )
    return sets, entropy, specificity


def random_sets(sets, layers, width):
    import torch

    gen = torch.Generator().manual_seed(SEED + 2)
    result = {}
    for k, data in sets.items():
        chosen = {lang: [] for lang in LANGS}
        for layer in range(layers):
            for lang in LANGS:
                count = data["layer_counts"][layer][lang]
                chosen[lang].extend(
                    (
                        torch.randperm(width, generator=gen)[:count] + layer * width
                    ).tolist()
                )
        result[k] = dict(
            flat_indices=chosen,
            layer_counts=data["layer_counts"],
            overlap_fraction=len(set(chosen[LANGS[0]]) & set(chosen[LANGS[1]]))
            / int(k),
        )
    return result


def scales(data, shape, gain, variant):
    import torch

    result = torch.ones(2, *shape)
    for j, lang in enumerate(LANGS):
        if variant == "both":
            result[j].flatten()[data["flat_indices"][lang]] *= 1 + gain
        result[j].flatten()[data["flat_indices"][LANGS[1 - j]]] *= (
            1 - gain if variant == "both" else 0
        )
    return result


def choose_grid(cells):
    return min(
        cells,
        key=lambda c: (
            -int(min(c["successes"].values()) >= 10),
            c["broken"],
            -min(c["successes"].values()),
            -sum(c["successes"].values()),
            c["k"],
            c["gain"],
            c["variant"] != "deactivate-other",
        ),
    )


class Engine:
    def __init__(self, start):
        import torch
        from transformers import AutoTokenizer, Qwen3ForCausalLM

        self.start = start
        self.deadline = start + GPU_SECONDS
        self.torch = torch
        self.device = torch.device("cuda")
        self.cap = CAP
        torch.manual_seed(SEED)
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL, local_files_only=True)
        self.model = (
            Qwen3ForCausalLM.from_pretrained(
                MODEL,
                dtype=torch.bfloat16,
                attn_implementation="sdpa",
                local_files_only=True,
            )
            .to(self.device)
            .eval()
        )
        assert all(
            p.device.type == "cuda" and p.device.index == 0
            for p in self.model.parameters()
        )
        assert (
            self.model.config.model_type == "qwen3"
            and self.model.config.num_hidden_layers == 36
        )
        self.hooks = NeuronHooks(
            [layer.mlp.down_proj for layer in self.model.model.layers]
        )
        eos = self.model.generation_config.eos_token_id
        self.eos = set(eos if isinstance(eos, list) else [eos])
        self.eos.add(self.tokenizer.eos_token_id)
        self.load_seconds = time.monotonic() - start

    def generate(self, messages, bias=None, capture=False):
        if time.monotonic() >= self.deadline - 30:
            raise BudgetStop("30-second reserve: no new request")
        torch = self.torch
        ids = self.tokenizer.apply_chat_template(
            messages, tokenize=True, add_generation_prompt=True, enable_thinking=False
        )
        inputs = torch.tensor([ids], device=self.device)
        h = self.hooks
        h.scale = (
            None
            if bias is None
            else bias.to(device=self.device, dtype=self.model.dtype)
        )
        h.capture = False
        if capture:
            h.reset_capture()
        generated, ended, cost_stop = [], False, False
        started = time.monotonic()
        with torch.inference_mode():
            h.prefill = True
            result = self.model(input_ids=inputs, use_cache=True, logits_to_keep=1)
            h.prefill = False
            for _ in range(self.cap):
                if time.monotonic() >= self.deadline - 2:
                    cost_stop = True
                    break
                token = int(result.logits[0, -1].argmax())
                generated.append(token)
                if token in self.eos:
                    ended = True
                    break
                # The generated token's own MLP position, not its predictor.
                # The final non-EOS token is also forwarded when profiling.
                if len(generated) < self.cap or capture:
                    h.capture = capture
                    result = self.model(
                        input_ids=torch.tensor([[token]], device=self.device),
                        past_key_values=result.past_key_values,
                        use_cache=True,
                        logits_to_keep=1,
                    )
            if self.device.type == "cuda":
                torch.cuda.synchronize()
        h.capture = False
        h.scale = None
        text = self.tokenizer.decode(generated, skip_special_tokens=True)
        record = dict(
            text=text,
            generated_token_ids=generated,
            input_token_ids=ids,
            eos=ended,
            truncated=not ended and len(generated) >= self.cap,
            cost_stopped=cost_stop,
            seconds=time.monotonic() - started,
            history=messages,
            input_sha256=hashlib.sha256(json.dumps(ids).encode()).hexdigest(),
        )
        profile = None
        if capture:
            count = len(generated) - int(ended)
            assert all(x == count for x in h.counts), (h.counts, count)
            profile = dict(frequency_sums=h.freqs.cpu(), count=count)
            record["profile_positions"] = count
        return record, profile


def bank():
    return base.bank()


def summarize(rows, eligibility=None):
    result = base.summarize(rows, eligibility)
    defaults = {r["task_id"]: r for r in rows if r["phase"] == "fresh_default"}
    nondefault = {}
    paired = {}
    for step in ("SET", "HOLD", "SWITCH", "BACK"):
        rs = [
            r
            for r in rows
            if r["phase"] == "screen"
            and r["arm"] == "shuffled"
            and r["step"] == step
            and r["task_id"] in defaults
        ]
        paired[step] = sum(
            defaults[r["task_id"]]["score"]["valid_language"] in LANGS for r in rs
        )
        nondefault[step] = sum(
            r["score"]["valid_language"] in LANGS
            and defaults[r["task_id"]]["score"]["valid_language"] in LANGS
            and r["score"]["valid_language"]
            != defaults[r["task_id"]]["score"]["valid_language"]
            for r in rs
        )
    result["shuffled_nondefault"] = nondefault
    result["shuffled_default_eligible_pairs"] = paired
    result["fresh_defaults"] = dict(
        Counter(r["score"]["valid_language"] or "broken" for r in defaults.values())
    )
    correct = result["arms"]["correct"]
    possible = (
        result["complete"]
        and correct["steps"]["SET"]["success"] >= 40
        and correct["steps"]["SWITCH"]["success"] >= 40
        and correct["broken_episodes"] <= 4
        and max(nondefault.values()) <= 8
        and correct["clear_impositions"] <= 8
    )
    result.pop("shuffled_worst_stage_javascript", None)
    result["verdict"] = (
        "INELIGIBLE"
        if eligibility
        else "PARTIAL"
        if not result["complete"]
        else "POSSIBLE"
        if possible
        else "MARGINAL"
        if correct["steps"]["SET"]["success"] >= 24
        else "NOT POSSIBLE"
    )
    return result


def status():
    processes = []
    for path in Path("/proc").iterdir():
        if not path.name.isdigit():
            continue
        try:
            args = (path / "cmdline").read_bytes().split(b"\0")
        except OSError:
            continue
        if (
            any(
                Path(a.decode(errors="replace")).name == "focus_check40.py"
                for a in args
            )
            and b"--mode" in args
            and b"run" in args
        ):
            processes.append(int(path.name))
    gpu = base.gpu_pids()
    reading = (ROOT / "results/quick-checks/check40/README.md").read_text()
    return dict(
        gpu_pids=gpu,
        check40_run_processes=processes,
        check40_terminal="## Observed results" in reading and "PENDING" not in reading,
        ready=not gpu and not processes,
        utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )


def save_report(summary):
    write_json(OUT / "summary.json", summary)
    lines = [
        "## Observed results",
        "",
        f"**{summary['verdict']}**; complete screen: {summary['complete']}; GPU allocation {summary.get('gpu_seconds', 0):.2f}/7200 seconds.",
        "",
        str(summary.get("stop_reason") or ""),
        str(summary.get("ineligible_reason") or ""),
        "",
        "| Arm | SET | HOLD | SWITCH | BACK | Broken episodes | CLEAR impositions |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for arm, a in summary["arms"].items():
        lines.append(
            f"| {arm} | "
            + " | ".join(
                f"{a['steps'][s]['success']}/64 (n={a['steps'][s]['n']})"
                for s in ("SET", "HOLD", "SWITCH", "BACK")
            )
            + f" | {a['broken_episodes']}/64 | {a['clear_impositions']}/64 ({a['clear_default_python']} eligible pairs) |"
        )
    lines += [
        "",
        "| Arm/stage | Task check | Target + task | Broken | Parse identity |",
        "|---|---:|---:|---:|---|",
    ]
    for arm, a in summary["arms"].items():
        for step, s in a["steps"].items():
            lines.append(
                f"| {arm}/{step} | {s['task_check']}/64 | {s['target_task_check']} | {s['broken']}/64 | {json.dumps(s['language_identity'])} |"
            )
    lines += [
        "",
        "Competence/defaults: `" + json.dumps(summary.get("competence", {})) + "`.",
        "",
        "Fresh screen defaults: `"
        + json.dumps(summary["fresh_defaults"])
        + "`; shuffled paired non-default counts: `"
        + json.dumps(summary["shuffled_nondefault"])
        + "`.",
    ]
    if (OUT / "neuron-sets.json").exists():
        sets = json.loads((OUT / "neuron-sets.json").read_text())["correct"]
        lines += [
            "",
            "| Layer | Python k200 | JS k200 | Python k500 | JS k500 | Python k1000 | JS k1000 |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
        for layer in range(len(sets["200"]["layer_counts"])):
            lines.append(
                f"| {layer} | "
                + " | ".join(
                    str(sets[str(k)]["layer_counts"][layer][lang])
                    for k in KS
                    for lang in LANGS
                )
                + " |"
            )
        lines += [
            "",
            "Set overlaps (intersection/k): `"
            + json.dumps({k: s["overlap_fraction"] for k, s in sets.items()})
            + "`.",
        ]
    if (OUT / "grid.json").exists():
        grid = json.loads((OUT / "grid.json").read_text())
        lines += [
            "",
            "Frozen cell: `" + json.dumps(grid.get("selected")) + "`.",
            "",
            "| k | g | Variant | Python /16 | JS /16 | Broken /32 |",
            "|---:|---:|---|---:|---:|---:|",
        ]
        for c in grid["cells"]:
            lines.append(
                f"| {c['k']} | {c['gain']} | {c['variant']} | {c['successes']['Python']} | {c['successes']['JavaScript']} | {c['broken']} |"
            )
    conclusions = dict(
        POSSIBLE="Scaling selected dense MLP neurons can address these two programming languages under this quick-check reading. This does not establish semantic program correctness or an automatic skill controller.",
        MARGINAL="Some language induction appeared, but the full feasibility reading failed.",
        INELIGIBLE="The eligibility gate failed; this run cannot decide whether selected neurons reliably address the languages.",
        PARTIAL="The screen is incomplete; its prefix cannot decide full-screen feasibility.",
    )
    conclusions["NOT POSSIBLE"] = (
        "This neuron-counting and scaling construction did not meet the pre-written feasibility threshold. This does not rule out other neuron selectors or interventions."
    )
    lines += ["", conclusions[summary["verdict"]], ""]
    other = ROOT / "results/quick-checks/check40/summary.json"
    c40 = json.loads(other.read_text()) if other.exists() else {}
    if c40.get("verdict") in ("POSSIBLE", "MARGINAL", "NOT POSSIBLE", "INELIGIBLE"):
        lines += [
            f"Check 40 currently reads **{c40['verdict']}** on Qwen3-30B-A3B router bias. Check 41 uses the task banks/checkers pinned to check 40 commit 531030a on dense Qwen3-4B MLP neurons; model size, architecture and intervention site differ, so this is not an isolated causal comparison."
        ]
    else:
        lines += [
            "Check 40 has no terminal feasibility reading yet; an empirical comparison is unavailable. Check 41 addresses dense MLP neurons, while check 40 addresses MoE routing on a different model."
        ]
    lines += [
        "",
        "records.jsonl preserves text, tokens, complete histories, parser/task/breakage flags and timing; profile task files preserve neuron counts in the original run. Generated programs are parsed, never executed.",
        "",
    ]
    (OUT / "README.md").write_text(
        (OUT / "prewritten-reading.md").read_text().split("\n## Results\n", 1)[0]
        + "\n\n"
        + "\n".join(lines)
    )


def grid_spec():
    return [
        dict(k=k, gain=g, variant=v)
        for k in KS
        for v, gains in (("both", (0.5, 1.0, 2.0)), ("deactivate-other", (1.0,)))
        for g in gains
    ]


def run():
    import torch

    assert status()["ready"], "GPU/check40 state changed after wait"
    assert not (OUT / "records.jsonl").exists(), (
        "Refuse overwrite/resume of model outcomes"
    )
    freeze = json.loads((OUT / "freeze.json").read_text())
    for name, digest in freeze["files"].items():
        assert sha(ROOT / name) == digest, f"Pre-outcome freeze drift: {name}"
    for name, entry in freeze["assets"].items():
        p = MODEL / name
        assert p.stat().st_size == entry["bytes"] and sha(p) == entry["sha256"], name
    assert status()["ready"], "Resources changed while checking assets"
    b = json.loads((OUT / "banks.json").read_text())
    rows, competence, eligibility, stop_reason = [], {}, None, None
    engine = None
    journal = (OUT / "records.jsonl").open("x")
    start = time.monotonic()
    write_json(
        OUT / "launch.json",
        dict(
            utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            freeze_sha256=sha(OUT / "freeze.json"),
            git_head=subprocess.check_output(
                ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
            ).strip(),
            seed=SEED,
        ),
    )

    def request(
        task,
        phase,
        arm,
        step,
        episode,
        cue=None,
        bias=None,
        history=None,
        capture=False,
    ):
        messages = base.messages_for(task, cue, history)
        rec, prof = engine.generate(messages, bias, capture)
        rec.update(
            phase=phase,
            arm=arm,
            step=step,
            episode=episode,
            task_id=task["id"],
            cue=cue,
            scaling_active=bias is not None,
            target=TARGETS.get(step),
        )
        rec["score"] = (
            score(rec["text"], task, rec["truncated"] or rec["cost_stopped"])
            if step != "NEUTRAL"
            else dict(neutral_ok=rec["text"].strip() == "OK")
        )
        if prof is not None:
            path = OUT / "profiles-by-task" / f"{arm}-{task['id']}.pt"
            path.parent.mkdir(exist_ok=True)
            torch.save(prof, path)
            rec["profile_file"] = str(path.relative_to(OUT))
            rec["profile_sha256"] = sha(path)
        journal.write(json.dumps(rec) + "\n")
        journal.flush()
        rows.append(rec)
        print(
            json.dumps(
                dict(
                    event="record",
                    n=len(rows),
                    phase=phase,
                    arm=arm,
                    step=step,
                    episode=episode,
                    language=rec["score"].get("language"),
                    seconds=round(rec["seconds"], 3),
                    elapsed=round(time.monotonic() - start, 2),
                )
            ),
            flush=True,
        )
        if rec["cost_stopped"]:
            raise BudgetStop("Cooperative per-token deadline")
        return rec, prof

    try:
        engine = Engine(start)
        write_json(
            OUT / "runtime.json",
            dict(
                torch=torch.__version__,
                load_seconds=engine.load_seconds,
                model_class=type(engine.model).__name__,
                dtype=str(engine.model.dtype),
                eos=sorted(engine.eos),
                layers=len(engine.hooks.projections),
                width=engine.hooks.projections[0].in_features,
            ),
        )
        for i, task in enumerate(b["competence"]):
            for lang in (*LANGS, None):
                request(task, "competence", lang or "OFF", "SET", i, cue=lang)
            if i == 0:
                # A charged first-task pilot, retained in competence, with no outcome-driven redesign.
                expected = (
                    32 * 3
                    + 32 * 2
                    + len(grid_spec()) * 16 * 2
                    + 64 * (1 + len(ARMS) * len(STEPS))
                )
                worst = max(r["seconds"] for r in rows)
                write_json(
                    OUT / "projection.json",
                    dict(
                        pilot_records=3,
                        total_requests=expected,
                        worst_request_seconds=worst,
                        projected_seconds=engine.load_seconds + 1.25 * expected * worst,
                        cap_seconds=GPU_SECONDS,
                        policy="fixed full design; cooperative cap can produce PARTIAL",
                    ),
                )
        for lang in LANGS:
            rs = [r for r in rows if r["phase"] == "competence" and r["arm"] == lang]
            competence[lang] = dict(
                valid=sum(r["score"]["valid_language"] == lang for r in rs),
                task_check=sum(
                    r["score"]["valid_task"] and r["score"]["valid_language"] == lang
                    for r in rs
                ),
                n=len(rs),
            )
        competence["default"] = dict(
            Counter(
                r["score"]["valid_language"] or "broken"
                for r in rows
                if r["phase"] == "competence" and r["arm"] == "OFF"
            )
        )
        write_json(OUT / "competence.json", competence)
        if any(competence[lang]["valid"] < 28 for lang in LANGS):
            eligibility = "competence: fewer than 28/32 valid unbroken outputs in at least one cued language"
            return
        aggregates, positions = [], []
        for lang in LANGS:
            total, count = None, 0
            for i, task in enumerate(b["profile"]):
                _, profile = request(
                    task, "profile", lang, "SET", i, cue=lang, capture=True
                )
                assert profile["count"] > 0, "Empty neuron profile"
                total = (
                    profile["frequency_sums"].clone()
                    if total is None
                    else total + profile["frequency_sums"]
                )
                count += profile["count"]
            aggregates.append(total.double() / count)
            positions.append(count)
        freq = torch.stack(aggregates)
        sets, entropy, specificity = select_neurons(freq)
        shuffled = random_sets(sets, *freq.shape[1:])
        torch.save(
            dict(
                languages=LANGS,
                frequencies=freq,
                positions=positions,
                entropy=entropy,
                specificity=specificity,
            ),
            OUT / "profiles.pt",
        )
        write_json(
            OUT / "neuron-sets.json",
            dict(
                correct=sets,
                shuffled=shuffled,
                shape=list(freq.shape[1:]),
                random_seed=SEED + 2,
                score="(f_lang-f_other)*(1-normalized_binary_entropy)",
            ),
        )
        if any(s["overlap_fraction"] > 0.5 for s in sets.values()):
            eligibility = "neuron sets overlap >50% for at least one pre-specified k"
            return
        cells = []
        for cell in grid_spec():
            normal = scales(
                sets[str(cell["k"])], freq.shape[1:], cell["gain"], cell["variant"]
            )
            successes, broken = dict.fromkeys(LANGS, 0), 0
            for i, task in enumerate(b["grid"]):
                for j, lang in enumerate(LANGS):
                    rec, _ = request(
                        task,
                        "grid",
                        f"{cell['k']}/{cell['gain']}/{cell['variant']}/{lang}",
                        "SET",
                        i,
                        bias=normal[j],
                    )
                    successes[lang] += rec["score"]["valid_language"] == lang
                    broken += rec["score"]["broken"]
            cells.append(dict(**cell, successes=successes, broken=broken))
            write_json(OUT / "grid.json", dict(cells=cells, frozen=False))
        selected = choose_grid(cells)
        write_json(
            OUT / "grid.json",
            dict(
                cells=cells,
                selected=selected,
                frozen=True,
                screen_records_at_freeze=0,
                utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            ),
        )
        normal = scales(
            sets[str(selected["k"])],
            freq.shape[1:],
            selected["gain"],
            selected["variant"],
        )
        shuf = scales(
            shuffled[str(selected["k"])],
            freq.shape[1:],
            selected["gain"],
            selected["variant"],
        )
        torch.save(
            dict(correct=normal, shuffled=shuf, selected=selected),
            OUT / "frozen-scales.pt",
        )
        neutral = dict(id="neutral", prompt="Reply only OK.", name="", witness="")
        # Observe all paired defaults before treatment: every stage has its exact fresh comparator.
        for e, task in enumerate(b["screen"]):
            request(task, "fresh_default", "OFF", "CLEAR", e)
        for e in range(64):
            task_indices = dict(
                zip(
                    ("SET", "HOLD", "SWITCH", "BACK", "CLEAR"),
                    ((e + offset) % 64 for offset in (0, 13, 26, 39, 52)),
                    strict=True,
                )
            )
            for arm in ARMS:
                history = [dict(role="system", content=base.SYSTEM)]
                for step in STEPS:
                    task = (
                        neutral
                        if step == "NEUTRAL"
                        else b["screen"][task_indices[step]]
                    )
                    lang = "JavaScript" if step == "NEUTRAL" else TARGETS[step]
                    bias = cue = None
                    if lang and arm in ("correct", "swapped", "shuffled"):
                        j = LANGS.index(lang)
                        bias = (
                            shuf[j]
                            if arm == "shuffled"
                            else normal[1 - j if arm == "swapped" else j]
                        )
                    if arm == "text-cue" and step != "NEUTRAL":
                        cue = lang
                    rec, _ = request(
                        task,
                        "screen",
                        arm,
                        step,
                        e,
                        cue=cue,
                        bias=bias,
                        history=history,
                    )
                    history = rec["history"] + [
                        dict(role="assistant", content=rec["text"])
                    ]
            partial = summarize(rows)
            partial.update(
                competence=competence,
                gpu_seconds=time.monotonic() - start,
                stop_reason="RUNNING",
            )
            write_json(OUT / "summary.json", partial)
    except BudgetStop as exc:
        stop_reason = str(exc)
    except Exception as exc:
        stop_reason = f"ERROR {type(exc).__name__}: {exc}"
        raise
    finally:
        journal.close()
        elapsed = time.monotonic() - start
        summary = summarize(rows, eligibility)
        summary.update(
            competence=competence,
            gpu_seconds=elapsed,
            gpu_cap_seconds=GPU_SECONDS,
            cap_overrun_seconds=max(0, elapsed - GPU_SECONDS),
            stop_reason=stop_reason,
            peak_memory_bytes=torch.cuda.max_memory_allocated()
            if engine is not None
            else None,
            freeze_sha256=sha(OUT / "freeze.json"),
            records_sha256=sha(OUT / "records.jsonl"),
        )
        save_report(summary)
        if engine is not None:
            engine.hooks.close()
        print(json.dumps(summary), flush=True)


def cpu_tests():
    import copy

    import torch
    from transformers import Qwen3Config, Qwen3ForCausalLM
    from transformers.models.qwen3.modeling_qwen3 import Qwen3MLP

    torch.set_num_threads(2)
    torch.manual_seed(SEED)
    checks = []
    config = Qwen3Config(
        hidden_size=8,
        intermediate_size=16,
        num_hidden_layers=2,
        num_attention_heads=2,
        num_key_value_heads=1,
        head_dim=4,
        vocab_size=32,
    )
    mlp = Qwen3MLP(config).eval()
    x = torch.randn(1, 3, 8)
    with torch.inference_mode():
        original = mlp(x)
        hooks = NeuronHooks([mlp.down_proj])
        assert torch.equal(mlp(x), original)
        assert hooks.hook(0)(mlp.down_proj, (x,)) is None
        product = mlp.act_fn(mlp.gate_proj(x)) * mlp.up_proj(x)
        hooks.scale = torch.ones(1, 16)
        hooks.scale[0, :8] = -1
        hooks.prefill = True
        altered = product.clone()
        altered[:, -1, :8] *= -1
        observed = mlp(x)
        assert torch.equal(observed, mlp.down_proj.forward(altered))
        assert torch.equal(observed[:, :-1], original[:, :-1])
        assert not torch.equal(observed[:, -1], original[:, -1])
        hooks.prefill = False
        observed = mlp(x)
        assert torch.equal(observed, mlp.down_proj.forward(product * hooks.scale[0]))
        hooks.scale = None
        hooks.reset_capture()
        hooks.capture = True
        for i in range(3):
            mlp(x[:, i : i + 1])
        assert hooks.counts == [3]
        assert torch.equal(hooks.freqs[0], (product > 0).sum((0, 1)))
        hooks.capture = False
        hooks.prefill = True
        mlp(x)
        assert hooks.counts == [3]
        assert torch.equal(mlp(x), original)
        hooks.close()
    checks.append(
        "real Qwen3MLP consumer: exact OFF; final prefill only; decode scaling; positive product counts excluding prompt"
    )
    model = Qwen3ForCausalLM(config).eval()
    tokens = torch.tensor([[1, 2, 3]])
    with torch.inference_mode():
        original = model(tokens).logits
        hooks = NeuronHooks([layer.mlp.down_proj for layer in model.model.layers])
        assert torch.equal(model(tokens).logits, original)
        hooks.scale = torch.zeros(2, 16)
        hooks.prefill = True
        changed = model(tokens).logits
        assert torch.equal(changed[:, :-1], original[:, :-1])
        assert not torch.equal(changed[:, -1], original[:, -1])
        hooks.scale = None
        assert torch.equal(model(tokens).logits, original)
        hooks.close()
    checks.append(
        "tiny CPU Qwen3ForCausalLM all-layer hooks change logits, preserve earlier prompt logits, restore exact OFF"
    )

    # Exercise the production decoding loop with a real tiny CPU trunk and scripted
    # token choice; the fixture controls tokens, not hook calls/cache progression.
    class TokenizerFixture:
        def apply_chat_template(self, messages, **kwargs):
            return [1, 2, 3]

        def decode(self, ids, **kwargs):
            return "fixture text"

    class ModelFixture:
        dtype = torch.float32

        def __init__(self, trunk, next_tokens):
            self.trunk, self.next_tokens, self.calls = trunk, iter(next_tokens), []

        def __call__(self, **kwargs):
            self.calls.append(kwargs["input_ids"].shape[-1])
            result = self.trunk(**kwargs)
            result.logits.fill_(-100)
            result.logits[..., next(self.next_tokens)] = 100
            return result

    e = Engine.__new__(Engine)
    e.start, e.deadline = time.monotonic(), time.monotonic() + 300
    e.torch, e.device, e.cap = torch, torch.device("cpu"), 3
    e.tokenizer, e.eos = TokenizerFixture(), {2}
    e.hooks = NeuronHooks([layer.mlp.down_proj for layer in model.model.layers])
    messages = [
        dict(role="system", content="fixture"),
        dict(role="user", content="fixture"),
    ]
    for next_tokens, eos, positions, calls in [
        ([4, 5, 2], True, 2, [3, 1, 1]),
        ([4, 5, 6, 7], False, 3, [3, 1, 1, 1]),
    ]:
        e.model = ModelFixture(model, next_tokens)
        rec, profile = e.generate(messages, capture=True)
        assert rec["eos"] == eos and rec["truncated"] != eos
        assert profile["count"] == rec["profile_positions"] == positions
        assert e.model.calls == calls and e.hooks.counts == [positions, positions]
        assert {
            "text",
            "generated_token_ids",
            "input_token_ids",
            "history",
            "seconds",
            "input_sha256",
            "cost_stopped",
        } <= rec.keys()
        assert rec["history"] == messages and profile["frequency_sums"].shape == (2, 16)
    e.hooks.close()
    checks.append(
        "production generation loop on CPU: EOS excluded, capped final token counted, prompt excluded, raw output/profile fields present"
    )
    f = torch.tensor(
        [
            [[0.9, 0.1, 0.5, 0.0], [0.8, 0.2, 0.5, 0.0]],
            [[0.1, 0.9, 0.5, 0.0], [0.2, 0.8, 0.5, 0.0]],
        ]
    )
    sets, entropy, specificity = select_neurons(f, (2,))
    assert sets["2"]["flat_indices"] == dict(Python=[0, 4], JavaScript=[1, 5])
    assert sets["2"]["overlap_fraction"] == 0 and entropy[:, 2:].eq(1).all()
    assert torch.allclose(specificity[0], -specificity[1])
    same, _, _ = select_neurons(torch.ones_like(f), (2,))
    assert same["2"]["overlap_fraction"] == 1
    random1 = random_sets(sets, 2, 4)
    torch.rand(10)
    assert random1 == random_sets(sets, 2, 4)
    for lang in LANGS:
        assert Counter(n // 4 for n in random1["2"]["flat_indices"][lang]) == Counter(
            {0: 1, 1: 1}
        )
    for gain in (0.5, 1, 2):
        v = scales(sets["2"], (2, 4), gain, "both")
        assert v[0, :, 0].eq(1 + gain).all() and v[0, :, 1].eq(1 - gain).all()
        assert v[1, :, 0].eq(1 - gain).all() and v[1, :, 1].eq(1 + gain).all()
        assert v[:, :, 2:].eq(1).all()
    v = scales(sets["2"], (2, 4), 1, "deactivate-other")
    assert v[0, :, 0].eq(1).all() and v[0, :, 1].eq(0).all()
    assert len(grid_spec()) == 12
    cells = [
        dict(
            k=200,
            gain=0.5,
            variant="both",
            successes=dict(Python=9, JavaScript=16),
            broken=0,
        ),
        dict(
            k=500,
            gain=1,
            variant="both",
            successes=dict(Python=10, JavaScript=10),
            broken=3,
        ),
    ]
    assert choose_grid(cells)["k"] == 500
    checks.append(
        "LAPE ranking, zero/tied frequencies, overlap, deterministic per-layer random sets, every gain including sign reversal, deactivation, grid priority"
    )
    task = dict(name="square", witness=r"\*")
    samples = [
        ("def square(x):\n    return x*x", "Python", True, False),
        ("function square(x) { return x*x; }", "JavaScript", True, False),
        ("```javascript\ndef square(x):\n    return x*x\n```", "Python", True, False),
        ("const square = x => x*x;", "JavaScript", True, False),
        ("def square(x):\n    pass", "Python", False, False),
        ("function square(x) { return x; }", "JavaScript", False, False),
        ("def other(x):\n    return x*x", "Python", False, False),
        ("42", "ambiguous", False, True),
        ("", "invalid", False, True),
        ("```python\ndef square(x):\n    return x*x", "invalid", False, True),
        ("function square( {", "invalid", False, True),
    ]
    for text, lang, coarse, broken in samples:
        result = score(text, task)
        assert (result["language"], result["task_check"], result["broken"]) == (
            lang,
            coarse,
            broken,
        ), result
    assert score(samples[0][0], task, True)["broken"]
    assert score("def square(x):\n" + "    print(x)\n" * 6 + "    return x*x", task)[
        "flags"
    ]["repetitive"]
    checks.append(
        "pinned parser/checker: languages, misleading labels, arrows, stubs, wrong name, ambiguity, invalid, fences, truncation, repetition"
    )
    b = bank()
    assert b == base.bank() == bank()
    assert [len(b[k]) for k in ("competence", "profile", "grid", "screen")] == [
        32,
        32,
        16,
        64,
    ]
    assert len({t["prompt"] for split in b.values() for t in split}) == 144
    assert all(len({(e + k) % 64 for k in (0, 13, 26, 39, 52)}) == 5 for e in range(64))
    history = [
        dict(role="system", content=base.SYSTEM),
        dict(role="user", content="old request"),
        dict(role="assistant", content="old answer"),
    ]
    assert base.messages_for(b["screen"][0], history=history)[:-1] == history
    checks.append(
        "committed check40 exact task bank, disjoint exact statements, distinct rotated episode tasks, complete history pairs"
    )

    def fake(lang, broken=False):
        return dict(
            language=lang,
            valid_language=None if broken else lang,
            valid_task=not broken,
            broken=broken,
        )

    rows = []
    for e in range(64):
        rows.append(dict(phase="fresh_default", task_id=str(e), score=fake("Python")))
        for arm in ARMS:
            for step in ("SET", "HOLD", "SWITCH", "BACK", "CLEAR"):
                lang = (
                    "Python" if step == "CLEAR" or arm == "shuffled" else TARGETS[step]
                )
                rows.append(
                    dict(
                        phase="screen",
                        arm=arm,
                        episode=e,
                        step=step,
                        task_id=str(e),
                        score=fake(lang),
                    )
                )
    assert summarize(rows)["verdict"] == "POSSIBLE"
    for target, count, expected in [
        ("SET", 40, "POSSIBLE"),
        ("SET", 39, "MARGINAL"),
        ("SET", 24, "MARGINAL"),
        ("SET", 23, "NOT POSSIBLE"),
        ("SWITCH", 39, "MARGINAL"),
    ]:
        changed = copy.deepcopy(rows)
        for r in changed:
            if (
                r["phase"] == "screen"
                and r["arm"] == "correct"
                and r["step"] == target
                and r["episode"] >= count
            ):
                r["score"] = fake(LANGS[1 - LANGS.index(TARGETS[target])])
        assert summarize(changed)["verdict"] == expected
    for mode, limits in [("breakage", (4, 5)), ("clear", (8, 9)), ("shuffled", (8, 9))]:
        for count in limits:
            changed = copy.deepcopy(rows)
            for r in changed:
                if r["phase"] != "screen" or r["episode"] >= count:
                    continue
                if mode == "breakage" and r["arm"] == "correct" and r["step"] == "HOLD":
                    r["score"] = fake("invalid", True)
                if mode == "clear" and r["arm"] == "correct" and r["step"] == "CLEAR":
                    r["score"] = fake("JavaScript")
                if mode == "shuffled" and r["arm"] == "shuffled" and r["step"] == "SET":
                    r["score"] = fake("JavaScript")
            assert summarize(changed)["verdict"] == (
                "POSSIBLE" if count == limits[0] else "MARGINAL"
            )
    assert summarize(rows[:-1])["verdict"] == "PARTIAL"
    assert summarize(rows, "overlap")["verdict"] == "INELIGIBLE"
    checks.append(
        "actual summary consumer: SET/SWITCH/breakage/CLEAR/shuffled exact boundary fixtures; partial and ineligible precedence"
    )
    assert not torch.cuda.is_initialized()
    return dict(
        passed=True,
        checks=checks,
        torch=torch.__version__,
        transformers=__import__("transformers").__version__,
        node=subprocess.check_output(["node", "--version"], text=True).strip(),
        mlp_source=inspect.getsource(Qwen3MLP),
        cuda_initialized=False,
    )


def prepare():
    assert not (OUT / "records.jsonl").exists(), "No preparation after model outcomes"
    assert (
        subprocess.check_output(
            ["git", "-C", str(ROOT), "show", "531030a:scripts/focus_check40.py"]
        )
        == (OUT / "check40-source.py.txt").read_bytes()
    ), "Pinned source must match requested commit"
    cpu = cpu_tests()
    write_json(OUT / "cpu.json", cpu)
    write_json(OUT / "banks.json", bank())
    reading = (OUT / "prewritten-reading.md").read_text()
    (OUT / "README.md").write_text(reading)
    assets = {
        p.name: dict(bytes=p.stat().st_size, sha256=sha(p))
        for p in MODEL.iterdir()
        if p.is_file()
        and (
            p.suffix in (".json", ".safetensors")
            or p.name in ("merges.txt", "vocab.json")
        )
    }
    names = ["scripts/focus_check41.py"] + [
        "results/quick-checks/check41/" + name
        for name in (
            "check40-source.py.txt",
            "banks.json",
            "prewritten-reading.md",
            "cpu.json",
        )
    ]
    write_json(
        OUT / "freeze.json",
        dict(
            seed=SEED,
            bank_source_seed=base.SEED,
            status="UNREGISTERED_PRE_OUTCOME_FREEZE",
            created_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            files={name: sha(ROOT / name) for name in names},
            assets=assets,
        ),
    )
    summary = summarize([])
    summary.update(
        stop_reason="PREPARED_WAITING_FOR_IDLE_GPU_AND_CHECK40", gpu_seconds=0
    )
    write_json(OUT / "summary.json", summary)
    print(json.dumps(cpu, indent=2), flush=True)


def audit():
    import torch

    rows = [
        json.loads(line) for line in (OUT / "records.jsonl").read_text().splitlines()
    ]
    existing = json.loads((OUT / "summary.json").read_text())
    recomputed = summarize(rows, existing["ineligible_reason"])
    for key in recomputed:
        assert recomputed[key] == existing[key], f"Summary mismatch: {key}"
    b = json.loads((OUT / "banks.json").read_text())
    tasks = {t["id"]: t for split in b.values() for t in split}
    for r in rows:
        if r["step"] != "NEUTRAL":
            assert (
                score(
                    r["text"], tasks[r["task_id"]], r["truncated"] or r["cost_stopped"]
                )
                == r["score"]
            ), r["task_id"]
        if r["phase"] == "screen":
            history = r["history"]
            assert history[0]["role"] == "system"
            assert [m["role"] for m in history[1:]] == [
                "user",
                "assistant",
            ] * STEPS.index(r["step"]) + ["user"]
            if r["step"] == "CLEAR":
                assert r["cue"] is None and not r["scaling_active"]
        if "profile_file" in r:
            assert sha(OUT / r["profile_file"]) == r["profile_sha256"]
            p = torch.load(OUT / r["profile_file"], weights_only=True)
            assert (
                p["count"]
                == r["profile_positions"]
                == len(r["generated_token_ids"]) - int(r["eos"])
            )
            assert (
                p["frequency_sums"].ge(0).all()
                and p["frequency_sums"].le(p["count"]).all()
            )
    if (OUT / "profiles.pt").exists():
        totals, counts = [], []
        for lang in LANGS:
            ps = [
                torch.load(OUT / r["profile_file"], weights_only=True)
                for r in rows
                if r["phase"] == "profile" and r["arm"] == lang
            ]
            count = sum(p["count"] for p in ps)
            totals.append(sum(p["frequency_sums"] for p in ps).double() / count)
            counts.append(count)
        prof = torch.load(OUT / "profiles.pt", weights_only=True)
        assert (
            torch.equal(torch.stack(totals), prof["frequencies"])
            and counts == prof["positions"]
        )
        sets, entropy, specificity = select_neurons(prof["frequencies"])
        saved = json.loads((OUT / "neuron-sets.json").read_text())
        assert (
            sets == saved["correct"]
            and random_sets(sets, *prof["frequencies"].shape[1:]) == saved["shuffled"]
        )
        assert torch.equal(entropy, prof["entropy"]) and torch.equal(
            specificity, prof["specificity"]
        )
    if (OUT / "grid.json").exists():
        grid = json.loads((OUT / "grid.json").read_text())
        for c in grid["cells"]:
            successes, broken = dict.fromkeys(LANGS, 0), 0
            for lang in LANGS:
                arm = f"{c['k']}/{c['gain']}/{c['variant']}/{lang}"
                rs = [r for r in rows if r["phase"] == "grid" and r["arm"] == arm]
                assert len(rs) == 16
                successes[lang] = sum(r["score"]["valid_language"] == lang for r in rs)
                broken += sum(r["score"]["broken"] for r in rs)
            assert c["successes"] == successes and c["broken"] == broken
        if grid["frozen"]:
            assert len(grid["cells"]) == 12 and grid["selected"] == choose_grid(
                grid["cells"]
            )
    write_json(
        OUT / "audit.json",
        dict(
            passed=True,
            rescored_records=len(rows),
            summary_exact=True,
            profiles_sets_grid_recomputed=True,
            records_sha256=sha(OUT / "records.jsonl"),
        ),
    )
    print("CPU raw-record audit passed.", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode", choices=["prepare", "test", "status", "run", "analyze"], required=True
    )
    parser.add_argument("--wait", action="store_true")
    args = parser.parse_args()
    if args.mode == "status":
        print(json.dumps(status(), indent=2))
    elif args.mode == "test":
        print(json.dumps(cpu_tests(), indent=2))
    elif args.mode == "prepare":
        with base.review_lock():
            prepare()
    elif args.mode == "analyze":
        with base.review_lock():
            audit()
    else:
        while True:
            state = status()
            print(json.dumps(state), flush=True)
            if state["ready"]:
                break
            assert args.wait, "GPU/check40 busy; --wait for 600-second polling"
            time.sleep(600)
        with base.review_lock():
            run()


if __name__ == "__main__":
    main()
