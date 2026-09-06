#!/usr/bin/env python3
"""FOCUS-3 foreground feasibility gate. No fitting, masking or sealed inputs."""

from __future__ import annotations

import argparse
import copy
import fcntl
import hashlib
import json
import os
import random
import subprocess
import time
from collections import Counter
from contextlib import contextmanager
from pathlib import Path

from stencil import focus2
from stencil import focus3 as f

ROOT = f.ROOT
OUT = ROOT / "results/quick-checks/focus3-gate"
CAP = 64
BUDGET = 10800
ARMS = ("C", "O", "N", "T")
FAMILIES = ("override", "cancel", "complete-and-move-on", "switch-and-return")
SYSTEM = (
    "Follow the user's currently applicable instructions. "
    "For a payload request with no applicable ordering rule, return the "
    "payload unchanged. Give only the requested answer; no explanation."
)
READING = """# FOCUS-3 gate — pre-written reading (2026-09-06)

Fit/train/select: NONE. Relations = frozen seed0 three GPU epochs, commit952079b8,
S/C/Cm/R=.94/.50/.50/.50; new-rule admission uses ft P(rule)>=.95 and every
eligible pair P(none)>=.98. The admission model has disclosed IFEval/probe
influence and an unreconciled historical recipe (data/classifier/LABELS.md).
This package is not development-independent. No sealed benchmark input is read.
Evaluation = new independent gpt-5.5-authored prose templates, seeded fresh
synthetic lists (30301 gate,30302 setup); template repetitions are disclosed,
so fixed-cohort feasibility counts are descriptive, not population inference.
Author fixture, generated inputs, source and all model/config hashes freeze in
Git before inference. No thresholds, prompts, cap, arm, or checker rescue.

64 gate episodes,16 each override/cancel/complete-and-move-on/switch-and-return;
16 setup episodes (4/family), all6 complete user+assistant pairs =12 turns.
Sort and JSON/tag obligations; every episode has quoted/hypothetical/tool-claim
hard-none prose, initial admission, change, unrefreshed continuation and final
request. Each list is distinct from its sorted/reversed forms. Setup and gate
use separate value ranges and authored scenario templates. All answers are fresh,
unscreened, greedy Qwen3-4B dense bf16 hf_compatible, thinking disabled, cap64.
Each arm owns its full conversation; ordinary fresh full-history prefill per
request, no masking, eviction, weight update, output sharing or forced successes.
This gate measures sort/tag compliance, not retained arbitrary-fact recall.

C: candidate sentence spans x eligible versions, frozen relation head, source
identity/explicit task-scope grammar, independent rule-head admission, register.
O: ground-truth admission and changes, same register and renderer. No gold goes
into C. N: no register or added text. T: append-only raw rule statements (gold
statement boundaries, no live-state decisions), including all superseded and
other-task rules; all ever-stated rules of the current request kind are rendered.
T receives no corrected live recap. C/O render inside EVERY task request's user
message; sort schema/tag constraints are absent on prose requests. Provenance
is logged with own-output intervals and live version sets, but never consumed.
Task switch suspends applicability; explicit return restores it. No masking
means mask un-release and affected masked-column counts are zero; switch-back
applicability/reactivated output-column counts and final success are separate.
Fail-safe none protects retirement only; confidently wrong none can permit bad
admission. Report admitted_beside_live separately from gold contradictory recaps.

Endpoints are episode counts: stale execution = any post-change sort answer
exactly executes an inapplicable old ordering on a pre-frozen discriminator;
false retirement = any gold-live row missing/changed/shadowed in C's rendered
set, INCLUDING initial admission misses; final success = final task answer and
tag exactly correct; breakage = any post-change invalid-schema/empty/truncated/
repetitive reply (FOCUS-2 JSON/equality/repetition primitives). Non-JSON prose is
allowed on prose turns; capped replies are broken, retained, never excluded.
REGISTER AGREEMENT compares source-turn/span IDs, version, scope, kind and text
at every task answer, including initial admission. Register-exact requires all
such turns equal. Contradictory recap = repeated evaluator gold key in one recap;
map all source spans to semantic order/tag keys before inference, including
hard-none cancellation claims, never supply that key map to C.

PASS requires ALL: absolute C/O stale-count distance<=4/64, absolute C/O final-
success distance<=4/64, C false retirements<=2/64, C breakage<=2/64, C stale<T
stale, C register-exact>=48/64 and>=12/16 in EVERY family, zero contradictory
recap episodes. N is descriptive; no retirement/agreement performance attributed
to N or T. These are practical margins, no statistical superiority claim.
All planned arms/turns required. O gold state/checkers must agree by CPU audit.
Missing work/budget -> INCOMPLETE; invariant/fail-open overflow -> FAIL. Setup
uses direct per-request current rule/tag cues and requires >=15/16 strict final
successes; failure -> INELIGIBLE and no gate. Setup scores do not filter episodes.
A failed completed gate stays FAIL; no output-based repair or rerun.

Cost before setup: at15 tokens/s,96 setup+1536 gate generations,64-token cap,
600s load and25% reserve:1.25*(600+1632*64/15)=9454s<10800s. Include classifier,
model load, setup and inference in elapsed GPU-held time. After all16 setup,
project from slowest full setup episode (including classification timing), four
arms/episode, plus already elapsed and25% reserve. Choose64 if within3h;
otherwise choose48 (12/family,first12 fixed indices) ONLY on this resource rule,
record selection before gate, and require36 exact/9 per family, margins3,
false retirement<=1,breakage<=1 (conservative floor of scaled2/64). If48 fails
projection, stop INCOMPLETE. Deadline checked before and within each generation;
no signals, retries or forced termination. Foreground only. GPU claim requires
empty nvidia-smi compute list and no results/quick-checks/*/RUNNING.flag, with
atomic flag under .review.lock; remove only our own flag after natural cleanup.

Required same-run records: exact user/rendered prompt, full prompt IDs, raw
reply/token IDs/EOS, score, gold/applied events, pair inputs/logits/probabilities,
admission diagnostics, before/after registers, C/O rendered sets/agreement,
provenance intervals/versions, switch-back flags/counts, timings. Per-episode
register traces and summaries accompany raw records. Source hashes checked at
launch and completion. PASS is feasibility on this frozen synthetic cohort only.
"""


def write(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w") as handle:
        json.dump(obj, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    tmp.replace(path)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def sources():
    paths = [
        ROOT / p
        for p in (
            "src/stencil/focus3.py",
            "scripts/focus3_gate.py",
            "tests/test_focus3_gate.py",
            "src/stencil/focus2.py",
            "src/stencil/qwen3.py",
            "models/qwen3-4b.pt",
            "models/qwen3-4b-hf/config.json",
            "models/qwen3-4b-hf/tokenizer.json",
        )
    ]
    for branch in ("relations", "ft"):
        paths.extend(
            p
            for p in (ROOT / "data/classifier/model" / branch).rglob("*")
            if p.is_file()
            and (
                p.parent.name == "encoder"
                or p.name
                in (
                    "head.pt",
                    "head.safetensors",
                    "thresholds.json",
                    "manifest.json",
                    "operating-point.json",
                )
            )
        )
    paths.extend(OUT / p for p in ("README.md", "authoring.json", "bank.json"))
    return {str(p.relative_to(ROOT)): digest(p) for p in paths}


def prepare(author):
    if (OUT / "freeze.json").exists():
        raise ValueError("already frozen; no overwrite")
    OUT.mkdir(parents=True, exist_ok=True)
    fixture = json.loads(Path(author).read_text())
    write(OUT / "authoring.json", fixture)
    bank = build_bank(fixture)
    validate_bank(bank)
    write(OUT / "bank.json", bank)
    (OUT / "README.md").write_text(READING)
    write(
        OUT / "freeze.json",
        dict(
            hashes=sources(),
            seed=30301,
            created=time.time(),
            reading=READING,
            model="Qwen3-4B",
            cap=CAP,
            gpu_cap=BUDGET,
        ),
    )
    print(
        json.dumps(dict(state="CPU_READY", setup=16, gate=64), sort_keys=True),
        flush=True,
    )


def validate_bank(bank):
    assert len(bank["gate"]) == 64 and len(bank["setup"]) == 16
    seen = set()
    for split in ("setup", "gate"):
        assert Counter(e["family"] for e in bank[split]) == dict.fromkeys(
            FAMILIES, 4 if split == "setup" else 16
        )
        for ep in bank[split]:
            assert 6 <= len(ep["turns"]) <= 12
            assert any(t["hard_none"] for t in ep["turns"])
            o = f.Oracle()
            for i, turn in enumerate(ep["turns"]):
                assert len(f.sentences(turn["text"])) <= 4, turn["text"]
                assert f.request_kind(turn["text"]) == turn["kind"]
                o.update(turn["text"], i, turn["events"])
                assert o.task == turn["task"], (ep["id"], i, o.task, turn["task"])
                if turn["kind"] == "sort":
                    value = turn["payload"]
                    assert tuple(value) not in seen
                    seen.add(tuple(value))
                    assert value != sorted(value) and value != sorted(
                        value, reverse=True
                    )
                    assert all(
                        focus2.target("sort", value, d)
                        != focus2.target("sort", value, turn["direction"])
                        for d in turn["stale"]
                    )
                    active = o.register.live(o.task, "sort")
                    orders = [
                        r for r in active if ep["gold_keys"][r.id].startswith("order:")
                    ]
                    assert len(orders) == (turn["direction"] != "default")
                    if orders:
                        assert turn["direction"] in orders[0].text
                    assert (
                        len([r for r in active if ep["gold_keys"][r.id] == "tag"]) == 1
                    )


def gold_pair_label(pair, turn):
    for event in turn["events"]:
        if (
            event.get("target") == pair["target_id"]
            and event["span"] == pair["target_span"]["text"]
        ):
            return event["label"]
    return "none"


def gpu_ready():
    running = sorted(
        str(p.relative_to(ROOT))
        for p in (ROOT / "results/quick-checks").glob("*/RUNNING.flag")
    )
    query = subprocess.run(
        [
            "nvidia-smi",
            "--query-compute-apps=pid,process_name",
            "--format=csv,noheader",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return not running and not query.stdout.strip(), dict(
        flags=running, compute=query.stdout.strip()
    )


@contextmanager
def claim_gpu():
    with (ROOT / ".review.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        ready, detail = gpu_ready()
        if not ready:
            raise RuntimeError("GPU busy: " + json.dumps(detail))
        with (OUT / "RUNNING.flag").open("x") as flag:
            json.dump(dict(pid=os.getpid(), check="FOCUS-3 gate"), flag)
            flag.flush()
            os.fsync(flag.fileno())
    try:
        yield
    finally:
        flag = OUT / "RUNNING.flag"
        if flag.exists() and json.loads(flag.read_text())["pid"] == os.getpid():
            flag.unlink()


class Trunk:
    def __init__(self, deadline):
        self.deadline = deadline
        self.tok = focus2.load_tokenizer(ROOT / "models/qwen3-4b-hf/tokenizer.json")
        self.backend = focus2.load_backend(
            self.tok,
            dict(
                config_path=ROOT / "models/qwen3-4b-hf/config.json",
                weights_path=ROOT / "models/qwen3-4b.pt",
            ),
        )

    def answer(self, history, text):
        start = time.monotonic()
        encode = lambda s: focus2.encode(self.tok, s)  # noqa: E731
        ids = encode("<|im_start|>system\n" + SYSTEM + "<|im_end|>\n")
        for old in history:
            ids += old["pair_ids"]
        prefix = encode(
            "<|im_start|>user\n" + text + "<|im_end|>\n"
            "<|im_start|>assistant\n<think>\n\n</think>\n\n"
        )
        ids += prefix
        if time.monotonic() >= self.deadline:
            raise TimeoutError("cooperative GPU deadline before prefill")
        cache = self.backend.empty()
        token = self.backend.forward(ids, cache)
        output, eos = [], None
        for index in range(CAP):
            if token in (focus2.EOS, focus2.END):
                eos = token
                break
            output.append(token)
            if time.monotonic() >= self.deadline:
                raise TimeoutError("cooperative GPU deadline during decode")
            if index + 1 < CAP:
                token = self.backend.decode(token, cache)
        text_out = self.tok.decode(output, skip_special_tokens=False)
        closure = [eos] + encode("\n") if eos == focus2.EOS else encode("<|im_end|>\n")
        pair = prefix + output + ([eos] if eos == focus2.END else []) + closure
        return dict(
            text=text_out,
            output_ids=output,
            eos=eos,
            prompt_ids=ids,
            pair_ids=pair,
            output_start=len(ids),
            seconds=time.monotonic() - start,
        )


def validate_record(r):
    fields = {
        "episode",
        "arm",
        "turn_index",
        "turn",
        "rendered_request",
        "generation",
        "score",
        "trace",
        "gold_trace",
        "gold_live",
        "live",
        "agreement",
        "provenance",
        "un_release",
        "classifier_seconds",
    }
    assert fields <= r.keys()
    assert r["generation"]["prompt_ids"] and r["generation"]["pair_ids"]
    assert r["generation"]["output_ids"] or r["generation"]["eos"] is not None
    assert r["provenance"]["mask_used"] is False


def run_episode(ep, arm, trunk, classifier, split):
    runtime, oracle = f.Runtime(classifier), f.Oracle()
    history, records, traces, ever = [], [], [], []
    prior_task = None
    visited = set()
    for i, turn in enumerate(ep["turns"]):
        kind = f.request_kind(turn["text"])
        gold_trace = oracle.update(turn["text"], i, turn["events"])
        gold_live = oracle.register.live(oracle.task, kind)
        classify_start = time.monotonic()
        trace = (
            runtime.update(turn["text"], i) if arm == "C" or split == "setup" else {}
        )
        classification_seconds = time.monotonic() - classify_start
        # Setup classifier work is timed but does not determine competence cues.
        if split == "setup":
            live = gold_live
        elif arm == "C":
            live = runtime.register.live(runtime.task, kind)
        elif arm == "O":
            live = gold_live
        elif arm == "N":
            live = []
        else:
            for event in turn["events"]:
                if event["label"] in ("admit", "supersedes"):
                    row = copy.deepcopy(
                        oracle.register.get(f"{i}:{turn['text'].index(event['span'])}")
                    )
                    ever.append(row)
            live = [r for r in ever if r.kind in ("all", kind)]
        rendered = (
            turn["text"]
            if arm == "N" and split != "setup"
            else f.render(turn["text"], live)
        )
        if (
            len(focus2.encode(trunk.tok, rendered))
            - len(focus2.encode(trunk.tok, turn["text"]))
            > 1024
        ):
            raise ValueError("renderer overflow: frozen fail-open counts FAIL")
        generation = trunk.answer(history, rendered)
        agreement = f.agreement(live, gold_live, ep["gold_keys"])
        selected = runtime.task if arm == "C" and split != "setup" else oracle.task
        returned = selected != prior_task and selected in visited
        reactivated = (
            sum(
                len(r["generation"]["output_ids"])
                + int(r["generation"]["eos"] is not None)
                for r in records
                if r["turn"]["task"] == selected
            )
            if returned
            else 0
        )
        for pair in trace.get("pairs", []):
            pair["gold"] = gold_pair_label(pair["input"], turn)
        record = dict(
            episode=ep["id"],
            family=ep["family"],
            arm=arm,
            split=split,
            turn_index=i,
            selected_task=selected,
            turn=turn,
            rendered_request=rendered,
            generation=generation,
            score=f.score(
                turn, generation["text"], generation["output_ids"], generation["eos"]
            ),
            trace=trace,
            gold_trace=gold_trace,
            gold_live=[f.wire(r) for r in gold_live],
            live=[f.wire(r) for r in live],
            agreement=agreement,
            classifier_seconds=classification_seconds,
            provenance=dict(
                origin="own_output",
                turn=i,
                versions=f.live_set(live),
                start=generation["output_start"],
                count=len(generation["output_ids"])
                + int(generation["eos"] is not None),
                mask_used=False,
            ),
            un_release=dict(
                task_return=returned,
                reactivated_output_columns=reactivated,
                masked_columns=0,
                mask_unrelease=False,
            ),
        )
        validate_record(record)
        path = OUT / split / "records" / f"{ep['id']}_{arm}_{i}.json"
        write(path, record)
        records.append(record)
        history.append(generation)
        visited.add(selected)
        prior_task = selected
        traces.append(
            {
                k: record[k]
                for k in (
                    "turn_index",
                    "trace",
                    "gold_trace",
                    "live",
                    "gold_live",
                    "agreement",
                    "un_release",
                )
            }
        )
        write(OUT / split / "traces" / f"{ep['id']}_{arm}.json", traces)
    return records


def diagnostics(records):
    result = {}
    for family in FAMILIES:
        rr = [r for r in records if r["family"] == family and r["arm"] == "C"]
        confusion = Counter(
            (p["gold"], p["applied"]) for r in rr for p in r["trace"]["pairs"]
        )
        result[family] = dict(
            pair_confusion={f"{a}->{b}": n for (a, b), n in confusion.items()},
            admitted_beside_live=sum(r["trace"]["admitted_beside_live"] for r in rr),
            overflow_turns=sum(r["trace"]["overflow"] for r in rr),
            pairs=sum(len(r["trace"]["pairs"]) for r in rr),
        )
    return result


def run():
    freeze = json.loads((OUT / "freeze.json").read_text())
    assert freeze["hashes"] == sources(), "frozen source/model/input drift"
    # Verify Git anchor before any classifier/trunk output, not just local receipt.
    for name in ("README.md", "freeze.json", "bank.json", "authoring.json"):
        path = str((OUT / name).relative_to(ROOT))
        committed = subprocess.run(
            ["git", "show", "HEAD:" + path], cwd=ROOT, check=True, capture_output=True
        ).stdout
        assert hashlib.sha256(committed).hexdigest() == digest(OUT / name)
    assert not (OUT / "started.json").exists(), "one-shot run already started"
    bank = json.loads((OUT / "bank.json").read_text())
    validate_bank(bank)
    with claim_gpu():
        started = time.monotonic()
        write(
            OUT / "started.json",
            dict(
                time=time.time(),
                pid=os.getpid(),
                commit=subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
                ).strip(),
            ),
        )
        trunk = None
        summary = dict(verdict="INCOMPLETE", reason="not completed")
        try:
            classifier = f.FrozenClassifier()
            trunk = Trunk(started + BUDGET - 30)
            setup, durations = [], []
            for ep in bank["setup"]:
                t = time.monotonic()
                records = run_episode(ep, "O", trunk, classifier, "setup")
                durations.append(time.monotonic() - t)
                setup.extend(records)
                print(
                    json.dumps(
                        dict(
                            stage="setup",
                            episode=ep["id"],
                            final=records[-1]["score"],
                            elapsed=time.monotonic() - started,
                        )
                    ),
                    flush=True,
                )
            competence = sum(
                f.episode_metrics([r for r in setup if r["episode"] == ep["id"]])[
                    "final_success"
                ]
                for ep in bank["setup"]
            )
            elapsed = time.monotonic() - started
            estimates = {n: elapsed + 1.25 * max(durations) * n * 4 for n in (64, 48)}
            selected_n = next(
                (n for n in (64, 48) if estimates[n] <= BUDGET - 30), None
            )
            selection = dict(
                competence=competence,
                required=15,
                durations=durations,
                projections=estimates,
                n=selected_n,
                elapsed=elapsed,
                written_before_gate=True,
                time=time.time(),
            )
            write(OUT / "selection.json", selection)
            if competence < 15:
                summary = dict(
                    verdict="INELIGIBLE", reason="setup competence", selection=selection
                )
            elif selected_n is None:
                summary = dict(
                    verdict="INCOMPLETE", reason="cost projection", selection=selection
                )
            else:
                episodes = [e for e in bank["gate"] if e["index"] < selected_n // 4]
                records = []
                rng = random.Random(30303)
                for ep in episodes:
                    order = list(ARMS)
                    rng.shuffle(order)
                    for arm in order:
                        records.extend(run_episode(ep, arm, trunk, classifier, "gate"))
                        print(
                            json.dumps(
                                dict(
                                    stage="gate",
                                    episode=ep["id"],
                                    arm=arm,
                                    elapsed=time.monotonic() - started,
                                )
                            ),
                            flush=True,
                        )
                summary = f.summarize(episodes, records, selected_n)
                summary["diagnostics"] = diagnostics(records)
                summary["selection"] = selection
                if any(r["trace"].get("overflow", False) for r in records):
                    summary.update(
                        verdict="FAIL", reason="classifier fail-open overflow"
                    )
                summary["record_count"] = len(records)
                summary["classifier_seconds"] = sum(
                    r["classifier_seconds"] for r in records
                )
                summary["peak_gpu_bytes"] = trunk.backend.peak_memory
        except TimeoutError as exc:
            summary = dict(verdict="INCOMPLETE", reason=str(exc))
        except Exception as exc:
            summary = dict(verdict="FAIL", reason=repr(exc))
            raise
        finally:
            if trunk is not None:
                trunk.backend.close()
            summary["gpu_held_seconds"] = time.monotonic() - started
            summary["freeze_sha256"] = digest(OUT / "freeze.json")
            summary["no_masking"] = True
            write(OUT / "summary.json", summary)
            print(json.dumps(summary, sort_keys=True), flush=True)
    assert sources() == freeze["hashes"], "source drift during run"


def build_bank(fixture):
    """Instantiate authored prose; events/checkers never enter Runtime."""
    bank = {}
    for split, seed, n in [("setup", 30302, 4), ("gate", 30301, 16)]:
        rng = random.Random(seed)
        episodes = []
        for family_index, family in enumerate(FAMILIES):
            templates = (
                fixture["setup_templates"][family_index : family_index + 1]
                if split == "setup"
                else fixture["families"][family.replace("-", "_")]
            )
            for index in range(n):
                template = templates[index % len(templates)]
                prefix = "S" if split == "setup" else "G"
                task_a = f"{prefix}{family_index}n{index}A"
                task_b = f"{prefix}{family_index}n{index}B"
                direction = template["direction"]
                opposite = template["opposite"]
                tag = (
                    rng.randrange(10, 90)
                    if split == "setup"
                    else rng.randrange(100, 900)
                )
                context = dict(
                    task_a=task_a,
                    task_b=task_b,
                    direction=direction,
                    opposite=opposite,
                    tag=tag,
                    receipt=f"word{prefix}{index}",
                )
                for key in (
                    "global_rule_template",
                    "initial_rule_template",
                    "hard_none_template",
                    "change_template",
                    "neutral_template",
                ):
                    context[key] = template[key].format(**context)
                ep = dict(
                    id=f"{split}_{family_index}_{index:02}",
                    seed=seed,
                    family=family,
                    index=index,
                    template=template["id"],
                    turns=[],
                    gold_keys={},
                )
                initial_id = None
                for ti, prose in enumerate(template["turn_templates"]):
                    other = ti >= 2 and family in (
                        "complete-and-move-on",
                        "switch-and-return",
                    )
                    task = task_b if other else task_a
                    if ti == 5 and family == "switch-and-return":
                        task = task_a
                    active = direction
                    if ti >= 2:
                        active = (
                            opposite
                            if family == "override"
                            else "default"
                            if family in ("cancel", "complete-and-move-on")
                            else direction
                            if ti == 5
                            else opposite
                        )
                    kind = "prose" if ti == 4 else "sort"
                    payload = rng.sample(
                        range(10, 90) if split == "setup" else range(100, 900), 5
                    )
                    while payload in (sorted(payload), sorted(payload, reverse=True)):
                        rng.shuffle(payload)
                    values = dict(context, task=task, payload=json.dumps(payload))
                    values["request"] = fixture["request_templates"][
                        "standard_sort"
                    ].format(**values)
                    final_key = (
                        "final_sort"
                        if "final_sort" in fixture["request_templates"]
                        else "standard_sort"
                    )
                    values["final_request"] = fixture["request_templates"][
                        final_key
                    ].format(**values)
                    text = prose.format(**values)
                    events = []
                    if ti == 0:
                        for key, scope, span in [
                            ("tag", "*", context["global_rule_template"]),
                            (
                                f"order:{task_a}",
                                task_a,
                                context["initial_rule_template"],
                            ),
                        ]:
                            events.append(
                                dict(
                                    label="admit",
                                    key=key,
                                    scope=scope,
                                    kind="sort",
                                    span=span,
                                )
                            )
                            ep["gold_keys"][f"0:{text.index(span)}"] = key
                        initial_id = f"0:{text.index(context['initial_rule_template'])}"
                    elif ti == 2:
                        if family == "switch-and-return":
                            span = (
                                f"For task {task_b}, sort the payload "
                                f"in {opposite} order."
                            )
                            events.append(
                                dict(
                                    label="admit",
                                    key=f"order:{task_b}",
                                    scope=task_b,
                                    kind="sort",
                                    span=span,
                                )
                            )
                        else:
                            label = {
                                "override": "supersedes",
                                "cancel": "cancels",
                                "complete-and-move-on": "completes",
                            }[family]
                            span = (
                                context["change_template"]
                                if family != "complete-and-move-on"
                                else f"Task {task_a} is complete."
                            )
                            events.append(
                                dict(
                                    label=label,
                                    target=initial_id,
                                    span=span,
                                    scope=task_a,
                                    kind="sort",
                                )
                            )
                    for event in events:
                        if event["label"] == "admit":
                            event["gold_key"] = event["key"]
                            event["key"] = f"new:{ti}:{text.index(event['span'])}"
                    for start, span in f.sentences(text):
                        rid = f"{ti}:{start}"
                        if any(
                            word in span.lower()
                            for word in (
                                "ascending",
                                "descending",
                                "cancel",
                                "complete",
                            )
                        ):
                            key_task = (
                                task_b
                                if (ti == 2 and family == "switch-and-return")
                                else task_a
                            )
                            ep["gold_keys"][rid] = f"order:{key_task}"
                        elif "keep tag equal" in span.lower():
                            ep["gold_keys"][rid] = "tag"
                        else:
                            ep["gold_keys"][rid] = "nonrule:" + rid
                    stale = []
                    if ti >= 2 and kind == "sort":
                        stale = [
                            d
                            for d in (direction, opposite)
                            if d != active
                            and (
                                d == direction
                                or family in ("override", "switch-and-return")
                            )
                        ]
                    ep["turns"].append(
                        dict(
                            text=text,
                            events=events,
                            kind=kind,
                            task=task,
                            direction=active,
                            tag=tag,
                            payload=payload,
                            stale=stale,
                            post_change=ti >= 2,
                            hard_none=ti == 1,
                        )
                    )
                episodes.append(ep)
        bank[split] = episodes
    return bank


def audit():
    """Replay saved bytes/state/scores only; never regenerate or invoke a model."""
    bank = json.loads((OUT / "bank.json").read_text())
    validate_bank(bank)
    freeze = json.loads((OUT / "freeze.json").read_text())
    assert sources() == freeze["hashes"]
    summary = json.loads((OUT / "summary.json").read_text())
    records = []
    for split in ("setup", "gate"):
        for ep in bank[split]:
            for arm in ("O",) if split == "setup" else ARMS:
                files = sorted(
                    (OUT / split / "records").glob(f"{ep['id']}_{arm}_*.json")
                )
                if not files:
                    continue
                assert len(files) == len(ep["turns"])
                o = f.Oracle()
                for path in files:
                    r = json.loads(path.read_text())
                    validate_record(r)
                    ti = r["turn_index"]
                    assert r["turn"] == ep["turns"][ti]
                    assert r["gold_trace"] == o.update(
                        r["turn"]["text"], ti, r["turn"]["events"]
                    )
                    assert r["gold_live"] == [
                        f.wire(v) for v in o.register.live(o.task, r["turn"]["kind"])
                    ]
                    g = r["generation"]
                    assert r["score"] == f.score(
                        r["turn"], g["text"], g["output_ids"], g["eos"]
                    )
                    records.append(r)
    gate = [r for r in records if r["split"] == "gate"]
    if summary["verdict"] in ("PASS", "FAIL") and "selection" in summary:
        n = summary["selection"]["n"]
        assert len(gate) == n * len(ARMS) * 6
        episodes = [e for e in bank["gate"] if e["index"] < n // 4]
        rebuilt = f.summarize(episodes, gate, n)
        for key in ("terms", "counts", "episodes"):
            assert rebuilt[key] == summary[key], key
        assert diagnostics(gate) == summary["diagnostics"]
    result = dict(
        audit="PASS",
        records=len(records),
        gate_records=len(gate),
        source_hashes_match=True,
        verdict=summary["verdict"],
    )
    write(OUT / "audit.json", result)
    print(json.dumps(result), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode", choices=("prepare", "ready", "run", "audit"), required=True
    )
    parser.add_argument("--author", default="/tmp/focus3_author.json")
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare(args.author)
    elif args.mode == "ready":
        print(json.dumps(gpu_ready()))
    elif args.mode == "run":
        run()
    else:
        audit()


if __name__ == "__main__":
    main()
