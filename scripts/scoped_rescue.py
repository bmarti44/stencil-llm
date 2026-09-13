"""The oracle-reminder rescue diagnostic (Astra forward review, step 3).

Sixteen development blocks x two matched applicability cases x two conditions =
64 short generations.  Condition `off` is ordinary recency context; condition
`oracle` supplies the applicable instruction VERBATIM FROM THE SOURCE MESSAGE in
the proposed reminder format, under the same context ceiling.  A block succeeds
only if both of its cases succeed.

The oracle supplies the instruction, never code, expected values or a gold patch.
It is a diagnostic condition and cannot become the shipped intervention.

Registration and prespecified readings: results/scoped/RESCUE-REGISTRATION.md.
NO GPU PROCESS MAY LAUNCH while Brian's standing pause is in force; `--stub`
exercises the whole pipeline on CPU with no model at all.

    uv run python scripts/scoped_rescue.py --stub --out /tmp/rescue.jsonl
    uv run python scripts/scoped_rescue.py --summarize --out results/scoped/rescue.jsonl
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stencil.scoped_blocks import (  # noqa: E402
    SUITES,
    entering_project,
    rescue_prompts,
    resolve,
)
from stencil.scoped_dev_blocks import BLOCKS  # noqa: E402

# registration section 4: frozen before any generation
CONDITIONS = ("off", "oracle")
MAX_NEW = 160            # a SHORT edit: one function of tens of tokens
CONTEXT_CEILING = 4096   # the shared GB10 rule, generation included
PROMPT_BUDGET = CONTEXT_CEILING - MAX_NEW
DEADLINE_S = 120.0       # short edits; the whole-file screen's 300 s does not apply
SCORE_TIMEOUT_S = 30.0
CONTENTION = 1.5          # the registered contention factor
CEILING_GPU_H = 0.5       # registered refusal above this projection
PILOT_CASES = 4           # the four longest-prompt cases, both conditions
HUB = str(ROOT / "deploy/stencil_focus/build/hub-4b")

FENCE = re.compile(r"```(?:[A-Za-z0-9_+-]*)\n(.*?)```", re.S)
KEEP = (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef,
        ast.ClassDef, ast.Assign, ast.AnnAssign)


def _line_slice(body: str, fname: str) -> str:
    """Last-resort slice for a reply that does not parse."""
    lines = body.splitlines()
    start = next((i for i, ln in enumerate(lines)
                  if ln.lstrip().startswith(f"def {fname}(")), None)
    if start is None:
        return ""
    indent = len(lines[start]) - len(lines[start].lstrip())
    out = [lines[start][indent:]]
    for ln in lines[start + 1:]:
        if ln.strip() and (len(ln) - len(ln.lstrip())) <= indent:
            break
        out.append(ln[indent:] if len(ln) > indent else ln.strip())
    return "\n".join(out).rstrip() + "\n"


def extract(text: str, fname: str) -> str:
    """The new definitions from the reply, with nothing executable at import time.

    Syntax-aware, because the line-based version had three defects: it dropped an
    `import` line above the function (leaving an undefined name), it took the
    FIRST fence even when the code was in the second, and it truncated a
    multiline `def` signature to `def fetch_rate(` (Astra, finding 9).

    Imports, helper definitions and constants the answer needs are kept;
    module-level calls and prose are dropped rather than executed.
    """
    fences = FENCE.findall(text)
    with_def = [f for f in fences
                if re.search(rf"^\s*def {re.escape(fname)}\(", f, re.M)]
    body = with_def[0] if with_def else (fences[0] if fences else text)
    try:
        tree = ast.parse(body)
    except SyntaxError:
        return _line_slice(body, fname)
    kept = [n for n in tree.body if isinstance(n, KEEP)]
    if not any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
               and n.name == fname for n in kept):
        return _line_slice(body, fname)
    parts = [ast.get_source_segment(body, n) for n in kept]
    return "\n\n".join(x for x in parts if x).rstrip() + "\n"


def score(block_id: str, case_index: int, source: str) -> dict:
    if not source.strip():
        return {"scores": dict.fromkeys(SUITES, False), "ok": False,
                "error": "no function in the reply"}
    try:
        proc = subprocess.run(  # noqa: S603 - fixed argv, untrusted on stdin
            [sys.executable, str(ROOT / "scripts/scoped_score_one.py")],
            input=json.dumps({"block": block_id, "case": case_index,
                              "source": source}),
            capture_output=True, text=True, timeout=SCORE_TIMEOUT_S, check=False,
        )
    except subprocess.TimeoutExpired:
        # the generation still happened and must be recorded, or a resume
        # regenerates it and the run silently pays twice
        return {"scores": dict.fromkeys(SUITES, False), "ok": False,
                "error": f"scorer exceeded {SCORE_TIMEOUT_S}s"}
    if proc.returncode != 0 or not proc.stdout.strip():
        return {"scores": dict.fromkeys(SUITES, False), "ok": False,
                "error": f"scorer exit {proc.returncode}: {proc.stderr[-400:]}"}
    return json.loads(proc.stdout)


def fingerprint(stub: bool, stub_mode: str, hub: str) -> dict:
    """What a record must match to be counted with the others.

    Astra's finding 5: records identified only by block/case/condition let a
    stub run, a different fixture, a different prompt builder or a different
    trunk be resumed into the same file and summarised together.
    """
    def sha(path):
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]
    return {
        "stub": bool(stub),
        "stub_mode": stub_mode if stub else "",
        "hub": "" if stub else hub,
        "blocks_sha": sha(ROOT / "src/stencil/scoped_dev_blocks.py"),
        "engine_sha": sha(ROOT / "src/stencil/scoped_blocks.py"),
        "runner_sha": sha(ROOT / "scripts/scoped_rescue.py"),
        "scorer_sha": sha(ROOT / "scripts/scoped_score_one.py"),
        "max_new": MAX_NEW,
        "prompt_budget": PROMPT_BUDGET,
        "deadline_s": DEADLINE_S,
    }


def read_records(path: Path):
    """Every complete JSONL record.  A partial trailing line from an interrupted
    append is skipped and reported rather than aborting the resume."""
    recs, partial = [], 0
    if not path.exists():
        return recs, partial
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            recs.append(json.loads(line))
        except json.JSONDecodeError:
            partial += 1
    return recs, partial


def pilot_items(token_len):
    """The four longest-prompt cases, which is what the registration names."""
    sized = []
    for block, index, case in items():
        built = rescue_prompts(block, case, token_len, PROMPT_BUDGET)
        sized.append((built["oracle"]["tokens"], block, index, case))
    sized.sort(key=lambda x: -x[0])
    return [(b, i, c) for _t, b, i, c in sized[:PILOT_CASES]]


def project(mean_s: float, n: int = 64) -> float:
    """Projected GPU-hours for the whole run, including the contention factor."""
    return CONTENTION * mean_s * n / 3600.0


def items():
    for block in BLOCKS:
        for index, case in enumerate(block.cases):
            yield block, index, case


def stub_reply(block, case, condition: str, mode: str) -> str:
    """CPU pipeline exercise with no model.  Three modes, all needed:

    `baseline` always answers with the package default -- deliberately wrong for
    most cases, because a stub that answered correctly would hide extraction and
    scoring defects behind a green summary.
    `correct` always answers gold: a POSITIVE control, without which a systematic
    extraction bug is indistinguishable from "the model cannot do it".
    `rescue` answers gold under the reminder and takes the newest-statement
    shortcut without it, so the decision arithmetic can be seen to report
    RESCUED when it should.
    """
    from stencil.scoped_blocks import p_always_newest, render_impl
    value, obs, _ = resolve(block.history, case.path, case.fn_kind)
    if mode == "correct" or (mode == "rescue" and condition == "oracle"):
        chosen = value
    elif mode == "rescue":
        chosen = p_always_newest(block, case)
    else:
        chosen = "default"
    return "```python\n" + render_impl(case.fname, case.fn_kind, chosen, obs) + "```"


def run(a) -> int:
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fp = fingerprint(a.stub, a.stub_mode, a.hub)
    run_id = hashlib.sha256(
        (json.dumps(fp, sort_keys=True) + str(time.time())).encode()
    ).hexdigest()[:12]
    existing, partial = read_records(out)
    if partial:
        print(f"note: {partial} incomplete line(s) in {out} skipped")
    stale = [r for r in existing if r.get("fingerprint") != fp]
    if stale:
        print(f"REFUSE: {len(stale)} record(s) in {out} were produced under a "
              f"different configuration; they cannot be resumed into this run. "
              f"Use a fresh --out path.")
        return 3
    done = {(r["block"], r["case"], r["condition"]) for r in existing}

    if a.stub:
        def token_len(text: str) -> int:
            return max(1, len(text) // 4)  # a stand-in, never used for a budget claim

        generate = None
    else:
        import os
        os.environ.setdefault("STENCIL_GPU_SHARE", "1")
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        tok = AutoTokenizer.from_pretrained(a.hub, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            a.hub, dtype=torch.bfloat16, device_map="cuda", trust_remote_code=True
        ).eval()
        eos = [tok.eos_token_id]

        def chat(text: str) -> str:
            """The shipped non-thinking chat template.

            Astra's finding 4: the registration says thinking is disabled, but
            the runner tokenized raw text and never applied the template, so
            there was no assistant boundary and no empty thinking block --
            a failure could have been raw-continuation formatting or reasoning
            eating the 160-token allowance.
            """
            return tok.apply_chat_template(
                [{"role": "user", "content": text}],
                tokenize=False, add_generation_prompt=True, enable_thinking=False,
            )

        def token_len(text: str) -> int:
            return len(tok(chat(text), add_special_tokens=False).input_ids)

        def generate(prompt: str) -> dict:
            ids = tok(chat(prompt), return_tensors="pt",
                      add_special_tokens=False).input_ids.to(model.device)
            assert ids.shape[1] <= PROMPT_BUDGET, ids.shape
            t0 = time.monotonic()
            with torch.no_grad():
                gen = model.generate(ids, attention_mask=torch.ones_like(ids),
                                     max_new_tokens=MAX_NEW, do_sample=False,
                                     eos_token_id=eos, pad_token_id=tok.pad_token_id,
                                     max_time=a.deadline)
            secs = time.monotonic() - t0
            new = gen[0, ids.shape[1]:].tolist()
            ended = bool(new) and new[-1] in eos
            return {
                "output": tok.decode([t for t in new if t not in eos],
                                     skip_special_tokens=True),
                "generated_tokens": len(new), "seconds": secs,
                "truncated": len(new) >= MAX_NEW and not ended,
                "timed_out": secs >= a.deadline,
            }

    todo = list(items())
    if a.pilot:
        todo = pilot_items(token_len)
        print(f"pilot: the {len(todo)} longest-prompt cases, both conditions "
              f"= {2 * len(todo)} generations")

    start, spent, timings = time.monotonic(), 0.0, []
    for block, index, case in todo:
        prompts = rescue_prompts(block, case, token_len, PROMPT_BUDGET)
        for condition in CONDITIONS:
            key = (block.id, index, condition)
            if key in done:
                continue
            elapsed_min = (time.monotonic() - start) / 60.0
            reserve_min = (a.deadline + SCORE_TIMEOUT_S) / 60.0
            if a.budget_min and elapsed_min + reserve_min > a.budget_min:
                print(f"INCOMPLETE: {elapsed_min:.1f} min spent of "
                      f"{a.budget_min}, and the next generation could need "
                      f"{reserve_min:.1f} more -- stopping before {key}")
                return 2
            built = prompts[condition]
            if a.stub:
                gen = {"output": stub_reply(block, case, condition, a.stub_mode),
                       "generated_tokens": 0,
                       "seconds": 0.0, "truncated": False, "timed_out": False}
            else:
                gen = generate(built["prompt"])
            spent += gen["seconds"]
            timings.append(gen["seconds"])
            source = extract(gen["output"], case.fname)
            result = score(block.id, index, source)
            want, obs, _ = resolve(block.history, case.path, case.fn_kind)
            rec = {
                "fingerprint": fp, "run": run_id,
                "block": block.id, "family": block.family, "case": index,
                "case_name": case.name, "condition": condition,
                "applicable": want, "obligations": list(obs),
                "prompt_tokens": built["tokens"],
                "reminder": built.get("reminder", ""),
                "kept_messages": built["kept"],
                "n_history": len(block.history),
                "output": gen["output"], "extracted": source,
                "generated_tokens": gen["generated_tokens"],
                "seconds": gen["seconds"], "truncated": gen["truncated"],
                "timed_out": gen["timed_out"],
                "scores": result["scores"], "ok": result["ok"],
                "error": result["error"],
                "invalid": not source.strip(),
            }
            with out.open("a") as fh:
                fh.write(json.dumps(rec) + "\n")
            print(f"{block.id} case{index} {condition:6} "
                  f"want={want:8} ok={result['ok']} {gen['seconds']:.1f}s")
    resident = (time.monotonic() - start) / 60.0
    print(f"complete: {spent / 60:.1f} generation-minutes, "
          f"{resident:.1f} resident minutes")
    if a.pilot and timings:
        mean_s = sum(timings) / len(timings)
        worst = max(timings)
        hours = project(mean_s)
        print(f"\nPILOT: mean {mean_s:.1f}s, max {worst:.1f}s per generation")
        print(f"projected full run = {CONTENTION} x {mean_s:.1f}s x 64 = "
              f"{hours:.3f} GPU-hours (generation only; loading and scoring are "
              f"on top, and the {len(timings)} pilot generations count toward it)")
        if hours > CEILING_GPU_H:
            print(f"REFUSE: {hours:.3f} GPU-hours exceeds the registered "
                  f"{CEILING_GPU_H} ceiling. Stop this design rather than "
                  f"trimming N, shortening max_new_tokens or dropping a "
                  f"condition after seeing the measurement.")
            return 4
        print(f"OK: under the registered {CEILING_GPU_H} GPU-hour ceiling.")
    return 0


def summarize(path: Path) -> int:
    recs, partial = read_records(path)
    if partial:
        print(f"note: {partial} incomplete line(s) skipped")

    # --- completeness FIRST.  Astra fed the old consumer a 48-record prefix and
    # --- it printed RESCUED, because a missing case silently became a failure.
    expected = {(b.id, i, c) for b in BLOCKS for i in (0, 1) for c in CONDITIONS}
    seen, duplicates = {}, []
    for r in recs:
        key = (r["block"], r["case"], r["condition"])
        if key in seen:
            duplicates.append(key)
        seen[key] = r
    fps = {json.dumps(r.get("fingerprint"), sort_keys=True) for r in recs}
    missing = sorted(expected - set(seen))
    problems = []
    if missing:
        problems.append(f"{len(missing)} of {len(expected)} records missing: "
                        f"{missing[:4]}{' ...' if len(missing) > 4 else ''}")
    if duplicates:
        problems.append(f"{len(duplicates)} duplicate key(s): {duplicates[:4]}")
    if len(fps) > 1:
        problems.append(f"{len(fps)} different configurations mixed in one file")
    stubbed = [r for r in recs if (r.get("fingerprint") or {}).get("stub")]

    by = seen
    rows = []
    for block in BLOCKS:
        got = {}
        for condition in CONDITIONS:
            cases = [by.get((block.id, i, condition)) for i in (0, 1)]
            got[condition] = all(c and c["ok"] and not c.get("timed_out")
                                 for c in cases)
        rows.append((block.id, got["off"], got["oracle"]))
    off_n = sum(1 for _b, o, _x in rows if o)
    oracle_n = sum(1 for _b, _o, x in rows if x)
    wins = [b for b, o, x in rows if x and not o]
    losses = [b for b, o, x in rows if o and not x]

    print(f"{'block':6} {'off':6} {'oracle':6}")
    for bid, o, x in rows:
        print(f"{bid:6} {str(o):6} {str(x):6}")
    print(f"\noff succeeds on {off_n}/16 blocks; oracle on {oracle_n}/16")
    print(f"wins (oracle only): {len(wins)} {wins}")
    print(f"losses (off only):  {len(losses)} {losses}")
    for condition in CONDITIONS:
        sub = [r for r in recs if r["condition"] == condition]
        if not sub:
            continue
        median = sorted(r["generated_tokens"] for r in sub)[len(sub) // 2]
        print(f"{condition:6} invalid {sum(r['invalid'] for r in sub)}/{len(sub)} "
              f"truncated {sum(r['truncated'] for r in sub)} "
              f"timed_out {sum(r['timed_out'] for r in sub)} "
              f"median tokens {median}")

    if problems:
        print("\nREADING: INCOMPLETE -- no efficacy reading is available:")
        for x in problems:
            print(f"  - {x}")
        print("  The registered N is 64 unique records from ONE configuration. "
              "An incomplete dataset stops here and is never rescued.")
        return 2
    if stubbed:
        print("\nREADING: STUB RUN -- these records came from --stub, not a "
              "model, and carry no evidence about efficacy.")
        return 0

    if off_n >= 12:
        print(f"\nCEILING: the off condition already succeeds on {off_n}/16 "
              f"blocks, so there is little headroom for a reminder to rescue. "
              f"If the reading below is NOT RESCUED it means the blocks are too "
              f"easy to measure this, NOT that the model cannot implement the "
              f"task; the two are not distinguishable from this design.")

    # the prespecified reading, registration section 7 -- not renegotiable here
    if oracle_n >= 12 and len(wins) >= 6 and len(losses) <= 1:
        print("\nREADING: RESCUED -- raise direction 1 from 28% to about 40%")
    elif oracle_n <= 8 or (len(wins) - len(losses)) <= 2:
        print("\nREADING: NOT RESCUED -- reduce to about 12% and stop this "
              "coding-workload direction under the present budget")
    else:
        print("\nREADING: INTERMEDIATE -- roughly 20-25%; do not launch the "
              "confirmation")
    print(f"exact two-sided paired sign test on the {len(wins)} wins and "
          f"{len(losses)} losses: p = {sign_p(len(wins), len(losses)):.4g}. "
          "These thresholds are investment rules, not significance tests.")
    return 0


def sign_p(wins: int, losses: int) -> float:
    """Exact two-sided binomial sign test on the discordant blocks."""
    n = wins + losses
    if n == 0:
        return 1.0
    from math import comb
    k = min(wins, losses)
    tail = sum(comb(n, i) for i in range(k + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(ROOT / "results/scoped/rescue.jsonl"))
    ap.add_argument("--hub", default=HUB)
    ap.add_argument("--deadline", type=float, default=DEADLINE_S)
    ap.add_argument("--budget-min", type=float, default=0.0)
    ap.add_argument("--stub", action="store_true",
                    help="no model: exercise packing, extraction and scoring on CPU")
    ap.add_argument("--stub-mode", default="baseline",
                    choices=("baseline", "correct", "rescue"))
    ap.add_argument("--summarize", action="store_true")
    ap.add_argument("--pilot", action="store_true",
                    help="the registered pilot: longest cases, then project and "
                         "refuse above the ceiling")
    a = ap.parse_args(argv)
    if a.summarize:
        return summarize(Path(a.out))
    assert entering_project(BLOCKS[0]), "fixture missing"
    return run(a)


if __name__ == "__main__":
    raise SystemExit(main())
