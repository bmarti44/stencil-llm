# ruff: noqa
"""LEDGER decider (LEDGER-PLAN.md): four arms on the Multi-IF replayed-history
harness, one difference per arm.

  base           recorded native (on disk, free)
  text_ledger    the SAME ledger entries re-appended verbatim (baseline to match)
  neural_ledger  ledger entries as sustained attention-bias targets via
                 select() — context UNCHANGED (context_tokens_added must be 0)
  specificity    matched bias mass on NON-ledger tokens

PRIMARY: Tango non-inferiority (margin 2.0 points, one-sided 95%) of
neural_ledger to text_ledger on per-constraint paired outcomes restricted to
the INSERTABLE families (obligation_gate.FIXABLE_FAMILIES); all families
reported as a secondary slice. The ledger is the aged entries (introduced in
an EARLIER turn) so both arms hold exactly the same set. Resumable with a
provenance check; atomic per-conversation records.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401

ARMS = ("text_ledger", "neural_ledger", "specificity")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="ledger-eval")
    p.add_argument("--diagnostic-only", action="store_true", help="only the disclosed diagnostic slice")
    p.add_argument("--limit", type=int, default=None, help="stop after N evaluable conversations (smoke)")
    p.add_argument("--top-k", type=int, default=2)
    p.add_argument("--dose", type=float, default=3.0)
    p.add_argument("--max-new", type=int, default=None)
    p.add_argument("--deadline", type=float, default=300.0)
    p.add_argument("--salience", choices=["auto", "heuristic"], default="auto",
                   help="auto = stencil.salience if importable else labelled heuristic")
    return p.parse_args()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def combined_sha(paths):
    d = hashlib.sha256()
    for path in paths:
        d.update(path.name.encode()); d.update(b"\0"); d.update(path.read_bytes()); d.update(b"\0")
    return d.hexdigest()


def atomic_json(path, value):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=1))
    tmp.rename(path)


def arm_branch(result, scores, *, context_tokens_added, **extra):
    return {
        "response": result.text,
        "response_sha256": hashlib.sha256(result.text.encode()).hexdigest(),
        "scores": scores,
        "per_constraint": [bool(x) for x in scores["inst_level_strict_acc"]],
        "strict": bool(scores["prompt_level_strict_acc"]),
        "n_generated": result.n_generated,
        "truncated": result.truncated,
        "timed_out": result.timed_out,
        "biased_tokens": result.biased_tokens,
        "context_tokens_added": context_tokens_added,
        **extra,
    }


def summarize(records, *, margin_points):
    """Paired per-constraint endpoints from the records on disk."""
    from stencil.e2_stats import mcnemar_one_sided
    from stencil.ledger import non_inferiority_summary, paired_drop_table

    cells = {"insertable": {a: [] for a in ("base",) + ARMS}, "all": {a: [] for a in ("base",) + ARMS}}
    cost = {a: [] for a in ("base",) + ARMS}
    turns = automatic_turns = empty_ledger_turns = 0
    selected_hist = {}
    for rec in records:
        for turn in rec["turns"].values():
            turns += 1
            automatic_turns += bool(turn["automatic"])
            empty_ledger_turns += not turn["aged_entry_indices"]
            for i in turn["arms"]["neural_ledger"]["selected_entries"]:
                key = turn["ledger"][i]["turn_introduced"]
                selected_hist[str(key)] = selected_hist.get(str(key), 0) + 1
            per = {"base": [bool(x) for x in turn["base"]["scores"]["inst_level_strict_acc"]]}
            per.update({a: turn["arms"][a]["per_constraint"] for a in ARMS})
            cost["base"].append(0)
            for a in ARMS:
                cost[a].append(turn["arms"][a]["context_tokens_added"])
            for j, ins in enumerate(turn["insertable"]):
                for a in per:
                    cells["all"][a].append(per[a][j])
                    if ins:
                        cells["insertable"][a].append(per[a][j])

    def pair(slice_, ref, cand):
        t = paired_drop_table(cells[slice_][ref], cells[slice_][cand])
        return {**t, "improve_points": (100.0 * (t["n01"] - t["n10"]) / t["n"]) if t["n"] else None,
                "mcnemar_improve_p": mcnemar_one_sided(t["n01"], t["n10"])}

    out = {"turns": turns, "automatic_turns": automatic_turns, "empty_ledger_turns": empty_ledger_turns,
           "automatic": turns > 0 and automatic_turns == turns,
           "selected_entries_by_turn_introduced": selected_hist,
           "context_tokens_added_mean": {a: (sum(v) / len(v) if v else None) for a, v in cost.items()},
           "context_tokens_added_max": {a: (max(v) if v else None) for a, v in cost.items()},
           "accuracy": {}}
    for slice_ in ("insertable", "all"):
        out["accuracy"][slice_] = {a: (sum(v) / len(v) if v else None) for a, v in cells[slice_].items()}
        out[f"primary_noninferiority_neural_vs_text[{slice_}]"] = non_inferiority_summary(
            cells[slice_]["text_ledger"], cells[slice_]["neural_ledger"], margin_points=margin_points)
        out[f"secondary_neural_vs_base[{slice_}]"] = pair(slice_, "base", "neural_ledger")
        out[f"secondary_text_vs_base[{slice_}]"] = pair(slice_, "base", "text_ledger")
        out[f"specificity_vs_base[{slice_}]"] = pair(slice_, "base", "specificity")
    primary = out["primary_noninferiority_neural_vs_text[insertable]"]
    out["primary_claim_valid"] = bool(out["automatic"] and primary.get("non_inferior")
                                      and out["context_tokens_added_max"]["neural_ledger"] == 0)
    if not out["automatic"]:
        out["primary_claim_note"] = "ledger built by the HEURISTIC fallback: NOT the automatic condition"
    return out


def main():
    args = parse_args()
    import torch
    from tokenizers import Tokenizer

    sys.path.insert(0, str(ROOT / "vendor"))
    import langdetect
    langdetect.DetectorFactory.seed = 0

    from stencil.bench import MAX_NEW
    from stencil.e2 import mass_matched_nonconstraint_control
    from stencil.e2_multiif import base_branch, build_replay_context, is_diagnostic_key, score_turn, turn_doc
    from stencil.ledger import (
        build_ledger, context_tokens_added, generate_sustained, heuristic_is_instruction,
        is_automatic, resolve_salience, select, text_ledger_context,
    )
    from stencil.obligation_gate import FIXABLE_FAMILIES
    from stencil.qwen3 import Qwen3
    from stencil.wave import WaveController

    max_new = args.max_new or MAX_NEW
    data_path = ROOT / "data" / "bench" / "multiif_en.jsonl"
    model_path = ROOT / "models" / "qwen3-1.7b.pt"
    controller_path = ROOT / "results" / "qwen" / "b3-ce-s0.pt"
    base_dir = ROOT / "results" / "qwen" / "b4-multiif-base"
    salience_path = ROOT / "src" / "stencil" / "salience.py"
    manifest = json.loads((ROOT / "data" / "bench" / "pins-manifest.json").read_text())
    if sha(data_path) != manifest["converted_sha256"]["multiif_en.jsonl"]:
        raise RuntimeError("Multi-IF data provenance mismatch")
    rows = [json.loads(line) for line in data_path.read_text().splitlines()]
    if len(rows) != 909:
        raise RuntimeError("registered Multi-IF cohort must contain 909 conversations")
    base_paths = [base_dir / f"conv-{i:03d}.json" for i in range(909)]
    base_records = [json.loads(p.read_text()) for p in base_paths]
    if any(r["ci"] != i for i, r in enumerate(base_records)):
        raise RuntimeError("base record order mismatch")

    sal = resolve_salience(heuristic_is_instruction if args.salience == "heuristic" else None)
    provenance = "heuristic" if args.salience == "heuristic" else sal.provenance
    note = sal.note or ("forced by --salience heuristic" if args.salience == "heuristic" else "")
    print(f"salience provenance: {provenance} {note}" + ("" if provenance == "salience" else "  (NOT the automatic condition)"), flush=True)

    outdir = ROOT / "results" / "qwen" / args.out
    outdir.mkdir(parents=True, exist_ok=True)
    meta = {
        "schema": 1,
        "data_sha256": sha(data_path),
        "base_records_sha256": combined_sha(base_paths),
        "model_sha256": sha(model_path),
        "controller_sha256": sha(controller_path),
        "ledger_module_sha256": sha(ROOT / "src" / "stencil" / "ledger.py"),
        "salience_module_sha256": sha(salience_path) if salience_path.exists() else None,
        "runner_sha256": sha(Path(__file__)),
        "salience_provenance": provenance,
        "salience_note": note,
        "automatic": provenance == "salience",
        "insertable_families": sorted(FIXABLE_FAMILIES),
        "diagnostic_only": bool(args.diagnostic_only),
        "top_k": args.top_k, "dose": args.dose, "max_new": max_new, "deadline": args.deadline,
        "margin_points": 2.0,
        "arms": ["base", *ARMS],
    }
    meta_path = outdir / "meta.json"
    if meta_path.exists():
        if json.loads(meta_path.read_text()) != meta:
            raise RuntimeError("evaluation resume provenance mismatch (delete the out dir or match the args)")
    else:
        atomic_json(meta_path, meta)

    tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
    model = Qwen3()
    model.load_state_dict(torch.load(model_path, map_location="cpu"), strict=True)
    model = model.to(torch.bfloat16).cuda().eval()
    ctrl = WaveController(beta_max=1.0).cuda()
    ctrl.load_state_dict(torch.load(controller_path, map_location="cpu"))
    ctrl = ctrl.eval()

    todo = [ci for ci, row in enumerate(rows) if not args.diagnostic_only or is_diagnostic_key(row["key"])]
    if args.limit is not None:
        todo = todo[: args.limit]
    for n_done, ci in enumerate(todo, start=1):
        row, base_record = rows[ci], base_records[ci]
        record_path = outdir / f"conv-{ci:03d}.json"
        if record_path.exists():
            continue
        present = [t for t in (1, 2, 3) if row[f"turn_{t}_prompt"]]
        prompts = [turn_doc(row, t)[0] for t in present]
        base_responses = [base_record["responses"][str(t)] for t in present]
        turns = {}
        for turn in [t for t in present if t >= 2]:
            context = build_replay_context(prompts, base_responses, turn=turn, positive_control=False)
            P = len(tok.encode(context).ids)
            _, current_ids, _ = turn_doc(row, turn)
            base = base_branch(base_record, turn)
            base["per_constraint"] = [bool(x) for x in base["scores"]["inst_level_strict_acc"]]
            base["strict"] = bool(base["scores"]["prompt_level_strict_acc"])
            base["context_tokens_added"] = 0

            entries = build_ledger(tok, context, model=model, salience=sal.classify)
            for e in entries:
                e.provenance = provenance  # honest label even when the fallback is forced
            aged_idx = [i for i, e in enumerate(entries) if e.turn_introduced < turn]
            aged = [entries[i] for i in aged_idx]

            # 2. text ledger: same entries re-appended verbatim, no bias
            text_ctx = text_ledger_context(context, aged)
            text = generate_sustained(model, tok, text_ctx, spans=[], max_new=max_new, deadline_s=args.deadline)
            text_arm = arm_branch(text, score_turn(row, turn, text.text),
                                  context_tokens_added=context_tokens_added(tok, context, text_ctx),
                                  selected_entries=list(aged_idx))

            # 3. neural ledger: select once from the prefill's final h20, sustain the bias
            chosen = []
            def select_fn(q):
                chosen.extend(select(aged, q, ctrl, top_k=args.top_k))
                return [e.span for e in chosen]
            neural = generate_sustained(model, tok, context, select_fn=select_fn, dose=args.dose,
                                        max_new=max_new, deadline_s=args.deadline)
            if (not neural.spans and max_new == MAX_NEW and not base["timed_out"]
                    and neural.text != base["response"]):
                raise RuntimeError(f"conv {ci} turn {turn}: silent neural arm differs from base (harness drift)")
            neural_arm = arm_branch(neural, score_turn(row, turn, neural.text), context_tokens_added=0,
                                    selected_entries=[entries.index(e) for e in chosen],
                                    selected_spans=[list(s) for s in neural.spans])

            # 4. specificity: matched bias mass on non-ledger tokens
            if neural.spans:
                control, control_dose = mass_matched_nonconstraint_control(
                    total_len=P, spans=neural.spans, target_dose=args.dose)
            else:
                control, control_dose = (), 0.0
            spec = generate_sustained(model, tok, context, spans=list(control), dose=control_dose,
                                      max_new=max_new, deadline_s=args.deadline)
            spec_arm = arm_branch(spec, score_turn(row, turn, spec.text), context_tokens_added=0,
                                  control_spans=[list(s) for s in control], control_dose=control_dose,
                                  selected_entries=[])

            turns[str(turn)] = {
                "context_sha256": hashlib.sha256(context.encode()).hexdigest(),
                "context_tokens": P,
                "instruction_ids": current_ids,
                "insertable": [iid in FIXABLE_FAMILIES for iid in current_ids],
                "ledger": [e.to_record() for e in entries],
                "aged_entry_indices": aged_idx,
                "automatic": is_automatic(entries) and provenance == "salience",
                "base": base,
                "arms": {"text_ledger": text_arm, "neural_ledger": neural_arm, "specificity": spec_arm},
            }
        if not turns:
            raise RuntimeError(f"conversation {ci}: no evaluable late turns")
        atomic_json(record_path, {"ci": ci, "key": row["key"], "diagnostic": is_diagnostic_key(row["key"]), "turns": turns})
        print(f"eval conversation {n_done}/{len(todo)} (ci={ci})", flush=True)

    records = [json.loads(p.read_text()) for p in sorted(outdir.glob("conv-*.json"))]
    summary = {**meta, "conversations_evaluated": len(records), **summarize(records, margin_points=2.0)}
    atomic_json(outdir / "summary.json", summary)
    print(json.dumps(summary, indent=1), flush=True)


if __name__ == "__main__":
    main()
