# ruff: noqa
"""LEDGER decider (LEDGER-PLAN.md, amended 2026-09-01 after
results/ledger-verify-sol.md): four arms on the Multi-IF replayed-history
harness, one difference per arm.

  base           recorded native (on disk, free)
  text_ledger    the SAME aged ledger entries re-appended verbatim (baseline to match)
  neural_ledger  aged ledger entries as sustained attention-bias targets via
                 select() — context UNCHANGED (context tokens MEASURED per turn)
  specificity    width- and position-matched NON-ledger spans, SAME dose

ESTIMAND: eligible outcomes = AGED (origin turn < current turn) constraints in
FIXABLE_FAMILIES; a neural pass is CREDITED only when the entry linked to that
constraint was selected.  PRIMARY: conversation-clustered one-sided 95% upper
bound on the mean paired difference (text - credited neural, points) < 2.0;
Tango on the pooled cells is descriptive only.  primary_claim_valid requires
the complete registered cohort, the frozen configuration, measured-zero neural
context tokens, <= 2% timeouts+truncations per arm, the real-salience
segmenter (identity asserted), text_ledger beating base on eligible outcomes,
an active ledger on every credited turn, and the clustered bound.  Resumable
with a fail-closed provenance check; atomic per-conversation records.

Round 2 (results/ledger-reverify-sol.md): every record must carry the cohort
identity (ci AND key from the data rows), the expected late turns, the full
arm set and an echo of the frozen configuration; the timeouts/truncations cap
binds base too; a majority of eligible constraints must have had their linked
entry selected (fail-closed credit alone lets concordant text failures pass);
the primary bound is the continuity-corrected clustered t bound (stats.py);
the specificity control never crashes (an impossible window is disclosed and
the turn excluded from neural-vs-specificity); the CPU preflight dry-constructs
that control for every ordered top_k selection of every turn.
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
# FROZEN (LEDGER-PLAN amendments): exploratory choices, not tuned after outcomes are viewed.
REGISTERED = {"top_k": 2, "dose": 3.0, "max_new": 1024, "deadline": 300.0}
REGISTERED_COHORT = 909
MARGIN_POINTS = 2.0
MAX_TIMEOUT_TRUNCATION_FRACTION = 0.02
SEGMENTER_IDENTITY = "stencil.salience.split_sentences"
PROVENANCE_FILES = {
    "salience_weights.json": ROOT / "src" / "stencil" / "salience_weights.json",
    "qwen3.py": ROOT / "src" / "stencil" / "qwen3.py",
    "ctrb.py": ROOT / "src" / "stencil" / "ctrb.py",
    "e2.py": ROOT / "src" / "stencil" / "e2.py",
    "e2_multiif.py": ROOT / "src" / "stencil" / "e2_multiif.py",
    "stats.py": ROOT / "src" / "stencil" / "stats.py",
    "ledger.py": ROOT / "src" / "stencil" / "ledger.py",
    "salience.py": ROOT / "src" / "stencil" / "salience.py",
    "wave.py": ROOT / "src" / "stencil" / "wave.py",                # WaveController (select's W_q/W_k)
    "bench.py": ROOT / "src" / "stencil" / "bench.py",              # EOS, WAVE_LAYERS, MAX_NEW
    "determinism.py": ROOT / "src" / "stencil" / "determinism.py",  # seeds / backend flags
    "tokenizer.json": ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json",
    "ledger_eval.py": Path(__file__).resolve(),
}
PROVENANCE_TREES = {"vendor/ifeval": ROOT / "vendor" / "ifeval"}


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="ledger-eval")
    p.add_argument("--diagnostic-only", action="store_true", help="only the disclosed diagnostic slice (falsification screen)")
    p.add_argument("--limit", type=int, default=None, help="stop after N evaluable conversations (smoke)")
    p.add_argument("--top-k", type=int, default=REGISTERED["top_k"])
    p.add_argument("--dose", type=float, default=REGISTERED["dose"])
    p.add_argument("--max-new", type=int, default=None)
    p.add_argument("--deadline", type=float, default=REGISTERED["deadline"])
    p.add_argument("--salience", choices=["auto", "heuristic"], default="auto",
                   help="auto = stencil.salience if importable else labelled heuristic")
    p.add_argument("--preflight-only", action="store_true", help="CPU: build every ledger, no model, then exit")
    return p.parse_args()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def combined_sha(paths):
    d = hashlib.sha256()
    for path in paths:
        d.update(path.name.encode()); d.update(b"\0"); d.update(path.read_bytes()); d.update(b"\0")
    return d.hexdigest()


def tree_sha(root):
    """Order-independent content hash of a source tree (relative path + bytes; no __pycache__)."""
    root = Path(root)
    files = sorted(p for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc")
    d = hashlib.sha256()
    for p in files:
        d.update(str(p.relative_to(root)).encode()); d.update(b"\0"); d.update(p.read_bytes()); d.update(b"\0")
    return d.hexdigest()


def provenance_manifest():
    out = {name: sha(path) for name, path in PROVENANCE_FILES.items()}
    out.update({name: tree_sha(path) for name, path in PROVENANCE_TREES.items()})
    return out


def atomic_json(path, value):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=1))
    tmp.rename(path)


def check_or_write_meta(meta_path, meta):
    """Resume fails CLOSED: any difference in meta (provenance hashes included) aborts."""
    if meta_path.exists():
        existing = json.loads(meta_path.read_text())
        if existing != meta:
            diff = sorted(k for k in set(existing) | set(meta) if existing.get(k) != meta.get(k))
            raise RuntimeError(f"evaluation resume provenance mismatch on {diff} (delete the out dir or match the args)")
    else:
        atomic_json(meta_path, meta)


def assert_real_segmenter(sal):
    """The runner's salience path must be the REAL one: sol found a bare callable
    silently resolving to the fallback segmenter (crash on conversation 769)."""
    from stencil import salience
    if sal.provenance != "salience" or sal.segment is not salience.split_sentences:
        raise RuntimeError(f"segmenter is not {SEGMENTER_IDENTITY}: provenance={sal.provenance!r} segment={sal.segment!r}")
    return SEGMENTER_IDENTITY


def diagnostic_indices(rows):
    from stencil.e2_multiif import is_diagnostic_key
    return [ci for ci, row in enumerate(rows) if is_diagnostic_key(row["key"])]


def present_turns(row):
    return [t for t in (1, 2, 3) if row[f"turn_{t}_prompt"]]


def late_turns(row):
    return [t for t in present_turns(row) if t >= 2]


def cohort_identity(rows):
    """The registered cohort as the data rows define it: per conversation index its key
    and the late turns a record MUST contain (summarize checks every record against it)."""
    return {ci: {"key": row["key"], "turns": [str(t) for t in late_turns(row)]} for ci, row in enumerate(rows)}


def turn_context(row, base_record, turn):
    """Exactly the context the runner sends (recorded base responses as history)."""
    from stencil.e2_multiif import build_replay_context, turn_doc
    present = present_turns(row)
    prompts = [turn_doc(row, t)[0] for t in present]
    responses = [base_record["responses"][str(t)] for t in present] if base_record is not None else [""] * len(present)
    return build_replay_context(prompts, responses, turn=turn, positive_control=False)


def turn_origins(row, turn):
    from stencil.e2_multiif import turn_doc
    from stencil.ledger import instruction_origins
    lists = {t: turn_doc(row, t)[1] for t in present_turns(row) if t <= turn}
    return instruction_origins(lists, current_turn=turn)


def constraint_rows(origins, insertable_families, selected_entry_indices):
    selected = set(selected_entry_indices)
    return [{"index": o["index"], "id": o["id"], "origin_turn": o["origin_turn"], "aged": bool(o["aged"]),
             "insertable": o["id"] in insertable_families, "entry_indices": list(o["entry_indices"]),
             "entry_selected": any(i in selected for i in o["entry_indices"])} for o in origins]


def dry_control_selections(aged_spans, top_k):
    """Every ORDERED choice of min(top_k, n) aged spans: select() can return any of them
    (score order matters for window allocation), so the preflight must survive each."""
    import itertools
    n = len(aged_spans)
    if n == 0:
        return []
    return [list(c) for c in itertools.permutations(aged_spans, min(top_k, n))]


def preflight(rows, tok, sal, todo, base_records=None, top_k=REGISTERED["top_k"]):
    """CPU, no model: build + link the ledger for every late turn of ``todo`` with the
    given salience AND dry-construct the specificity control for every ordered top_k
    selection of aged entries (sol round 2: conversation 145 turn 2 crashed the arm);
    any exception is re-raised with the conversation/turn named, an impossible control
    window is counted and listed."""
    from stencil import ledger as ledger_module
    from stencil import salience as salience_module
    from stencil.e2 import user_turn_span_records
    from stencil.ledger import build_ledger, link_entries
    from stencil.obligation_gate import FIXABLE_FAMILIES
    stats = {"conversations": 0, "turns": 0, "entries": 0, "aged_entries": 0, "turns_with_aged_entries": 0,
             "turns_with_aged_constraints": 0, "eligible_constraints": 0, "linkage_granularity": {}, "errors": [],
             "segmenter": (SEGMENTER_IDENTITY if sal.segment is salience_module.split_sentences  # identity, not label
                           else f"{sal.segment.__module__}.{sal.segment.__name__}"),
             "control_top_k": top_k, "control_dry_runs": 0, "control_incomplete_turns": [], "control_incomplete_turn_count": 0}
    for ci in todo:
        row = rows[ci]
        base_record = base_records[ci] if base_records is not None else None
        stats["conversations"] += 1
        for turn in late_turns(row):
            try:
                context = turn_context(row, base_record, turn)
                entries = build_ledger(tok, context, salience=sal)
                origins = turn_origins(row, turn)
                gran = link_entries(entries, tok, context, origins)
                rows_ = constraint_rows(origins, FIXABLE_FAMILIES, [])
                aged = [e for e in entries if e.turn_introduced < turn]
                P = len(tok.encode(context).ids)
                user_turns = [tuple(r["span"]) for r in user_turn_span_records(tok, context)]
                incomplete = False
                for selected in dry_control_selections([e.span for e in aged], top_k):
                    control, tiers = ledger_module.matched_nonledger_control(
                        total_len=P, selected=selected, ledger_spans=[e.span for e in entries], user_turns=user_turns)
                    stats["control_dry_runs"] += 1
                    if len(control) != len(selected) or len(tiers) != len(selected):
                        raise RuntimeError("control/tier lists do not align with the selection")
                    incomplete = incomplete or any(t == "none" for t in tiers)
            except Exception as exc:
                raise RuntimeError(f"preflight failed at ci={ci} turn={turn}: {exc.__class__.__name__}: {exc}") from exc
            if incomplete:
                stats["control_incomplete_turns"].append({"ci": ci, "turn": turn})
                stats["control_incomplete_turn_count"] += 1
            stats["turns"] += 1
            stats["entries"] += len(entries)
            stats["aged_entries"] += len(aged)
            stats["turns_with_aged_entries"] += bool(aged)
            stats["turns_with_aged_constraints"] += any(c["aged"] for c in rows_)
            stats["eligible_constraints"] += sum(c["aged"] and c["insertable"] for c in rows_)
            stats["linkage_granularity"][gran] = stats["linkage_granularity"].get(gran, 0) + 1
    return stats


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
        "prompt_tokens": result.prompt_tokens,
        "context_tokens_added": context_tokens_added,
        "context_tokens_measured": True,
        **extra,
    }


# ------------------------------------------------------------------ summary
def outcome_rows(turn):
    """Per-constraint rows of one turn record.  eligible = aged AND insertable
    (the primary estimand); neural credit requires the linked entry selected."""
    base = turn["base"]["per_constraint"]
    per = {a: turn["arms"][a]["per_constraint"] for a in ARMS}
    rows = []
    for c in turn["constraints"]:
        j = c["index"]
        eligible = bool(c["aged"] and c["insertable"])
        neural_raw = bool(per["neural_ledger"][j])
        neural = neural_raw and bool(c["entry_selected"])
        rows.append({"id": c["id"], "origin_turn": c["origin_turn"], "aged": bool(c["aged"]), "insertable": bool(c["insertable"]),
                     "eligible": eligible, "entry_selected": bool(c["entry_selected"]),
                     "base": bool(base[j]), "text": bool(per["text_ledger"][j]), "neural_raw": neural_raw,
                     "neural": neural, "specificity": bool(per["specificity"][j]),
                     "diff_points": 100.0 * (float(per["text_ledger"][j]) - float(neural))})
    return rows


def _pair(ref, cand):
    from stencil.e2_stats import mcnemar_one_sided
    from stencil.ledger import paired_drop_table
    t = paired_drop_table(ref, cand)
    return {**t, "improve_points": (100.0 * (t["n01"] - t["n10"]) / t["n"]) if t["n"] else None,
            "mcnemar_improve_p_exploratory": mcnemar_one_sided(t["n01"], t["n10"])}


def _rate(xs):
    return (sum(xs) / len(xs)) if xs else None


def summarize(records, meta, *, cohort_size, identity, margin_points=MARGIN_POINTS):
    """Every endpoint from the records on disk; the validity gate is ALL-of.  ``identity``
    is ``cohort_identity(rows)``: every record is checked against it (ci, key, expected
    late turns), for its arm set and for its echo of the frozen configuration."""
    from stencil.ledger import non_inferiority_summary
    from stencil.stats import clustered_bound

    arms = ("base",) + ARMS
    cells_all = {a: [] for a in arms}
    elig = {a: [] for a in arms}
    elig_unselected = {"text": [], "neural_raw": []}
    cost = {a: [] for a in arms}
    measured = {a: True for a in ARMS}
    bad_gen = {a: 0 for a in arms}
    turns = automatic_turns = empty_ledger_turns = credited_turns = credited_turns_active = 0
    control_incomplete_turns = 0
    selected_hist = {}
    per_conv_diff, per_conv_spec = {}, {}
    cis = [r["ci"] for r in records]
    identity_ok = arm_set_ok = config_ok = turns_ok = True
    for rec in records:
        ident = identity.get(rec.get("ci"))
        identity_ok = identity_ok and ident is not None and rec.get("key") == ident["key"]
        turns_ok = turns_ok and ident is not None and sorted(rec["turns"]) == sorted(ident["turns"]) and bool(ident["turns"])
        arm_set_ok = arm_set_ok and set(rec.get("arms", [])) == set(arms)
        config_ok = config_ok and rec.get("config") == REGISTERED
        for turn in rec["turns"].values():
            if set(turn["arms"]) != set(ARMS):
                arm_set_ok = False
                continue
            turns += 1
            automatic_turns += bool(turn["automatic"])
            empty_ledger_turns += not turn["aged_entry_indices"]
            for i in turn["arms"]["neural_ledger"]["selected_entries"]:
                key = str(turn["ledger"][i]["turn_introduced"])
                selected_hist[key] = selected_hist.get(key, 0) + 1
            cost["base"].append(0)
            for a in ARMS:
                arm = turn["arms"][a]
                cost[a].append(arm["context_tokens_added"])
                measured[a] = measured[a] and bool(arm.get("context_tokens_measured", False))
                bad_gen[a] += bool(arm["timed_out"]) or bool(arm["truncated"])
            bad_gen["base"] += bool(turn["base"].get("timed_out")) or bool(turn["base"].get("truncated"))
            spec_arm = turn["arms"]["specificity"]
            control_incomplete = bool(spec_arm.get("control_incomplete")) or "none" in spec_arm.get("control_tiers", [])
            control_incomplete_turns += control_incomplete
            rows = outcome_rows(turn)
            for r in rows:
                cells_all["base"].append(r["base"]); cells_all["text_ledger"].append(r["text"])
                cells_all["neural_ledger"].append(r["neural_raw"]); cells_all["specificity"].append(r["specificity"])
                if r["eligible"]:
                    elig["base"].append(r["base"]); elig["text_ledger"].append(r["text"])
                    elig["neural_ledger"].append(r["neural"]); elig["specificity"].append(r["specificity"])
                    per_conv_diff.setdefault(rec["ci"], []).append(r["diff_points"])
                    if not control_incomplete:  # a turn without a full matched control is not a specificity comparison
                        per_conv_spec.setdefault(rec["ci"], []).append(100.0 * (float(r["neural_raw"]) - float(r["specificity"])))
                    if not r["entry_selected"]:
                        elig_unselected["text"].append(r["text"]); elig_unselected["neural_raw"].append(r["neural_raw"])
            if any(r["eligible"] for r in rows):
                credited_turns += 1
                credited_turns_active += bool(turn["ledger_active"])

    conv_means = [_rate(v) for _, v in sorted(per_conv_diff.items())]
    spec_means = [_rate(v) for _, v in sorted(per_conv_spec.items())]
    primary_bound = clustered_bound(conv_means, alpha=0.05)
    spec_upper = clustered_bound(spec_means, alpha=0.05)
    spec_lower = clustered_bound([-x for x in spec_means], alpha=0.05)
    n_elig = len(elig["text_ledger"])
    text_vs_base = _pair(elig["base"], elig["text_ledger"]) if n_elig else None
    bad_frac = {a: (bad_gen[a] / turns if turns else None) for a in arms}
    bad_ok = {a: (turns > 0 and bad_frac[a] <= MAX_TIMEOUT_TRUNCATION_FRACTION) for a in arms}  # EVERY arm, base included
    n_selected = n_elig - len(elig_unselected["text"])
    registered = meta.get("registered", REGISTERED)
    expected_turns = sum(len(v["turns"]) for v in identity.values())
    validity = {
        "complete_cohort": len(records) == cohort_size and len(set(cis)) == len(cis) and turns > 0,
        "registered_cohort": cohort_size == REGISTERED_COHORT and len(identity) == REGISTERED_COHORT,
        "records_identity": bool(records) and identity_ok and set(cis) == set(identity),
        "expected_turns_present": bool(records) and turns_ok and turns == expected_turns,
        "records_arm_set": bool(records) and arm_set_ok,
        "records_echo_registered_config": bool(records) and config_ok,
        "registered_config": all(meta.get(k) == v for k, v in REGISTERED.items()) and registered == REGISTERED,
        "neural_context_tokens_measured_zero": measured["neural_ledger"] and turns > 0 and sum(cost["neural_ledger"]) == 0,
        "timeouts_truncations_le_2pct": turns > 0 and all(bad_ok.values()),
        "timeouts_truncations_per_arm": bad_ok,
        "real_salience_segmenter": (meta.get("automatic") is True and meta.get("salience_provenance") == "salience"
                                    and meta.get("segmenter") == SEGMENTER_IDENTITY
                                    and meta.get("segmenter_identity_asserted") is True
                                    and turns > 0 and automatic_turns == turns),
        "text_beats_base": bool(text_vs_base and text_vs_base["n01"] > text_vs_base["n10"]),
        "ledger_active_on_credited_turns": credited_turns > 0 and credited_turns_active == credited_turns,
        # sol round 2: turn-level activity is not enough — with half the eligible cells never
        # exercising the ledger (and text failing the same half) the claim passed.  Registered
        # conservative reading: the linked entry must have been selected on a MAJORITY of
        # eligible constraints (strict), else the estimand is dominated by untested cells.
        "ledger_selected_on_majority_of_eligible": n_elig > 0 and 2 * n_selected > n_elig,
        "clustered_bound_below_margin": primary_bound["upper_bound"] is not None and primary_bound["upper_bound"] < margin_points,
    }
    validity_gate = {k: v for k, v in validity.items() if k != "timeouts_truncations_per_arm"}
    out = {
        "turns": turns, "automatic_turns": automatic_turns, "empty_ledger_turns": empty_ledger_turns,
        "credited_turns": credited_turns, "credited_turns_ledger_active": credited_turns_active,
        "automatic": turns > 0 and automatic_turns == turns,
        "selected_entries_by_turn_introduced": selected_hist,
        "context_tokens_added_mean": {a: _rate(v) for a, v in cost.items()},
        "context_tokens_added_max": {a: (max(v) if v else None) for a, v in cost.items()},
        "context_tokens_added_sum": {a: sum(v) for a, v in cost.items()},
        "context_tokens_measured": measured,
        "timeouts_or_truncations": bad_gen, "timeouts_or_truncations_fraction": bad_frac,
        "eligible": {
            "definition": "aged (origin turn < current turn) AND insertable family; neural credited only if its linked entry was selected",
            "n": n_elig, "n_conversations": len(per_conv_diff),
            "n_unselected": len(elig_unselected["text"]),
            "selected_fraction": (n_selected / n_elig) if n_elig else None,
            "unselected_slice": ({"text_pass_rate": _rate(elig_unselected["text"]), "neural_raw_pass_rate": _rate(elig_unselected["neural_raw"])}),
            "accuracy": {a: _rate(v) for a, v in elig.items()},
        },
        "primary": {
            "estimand": "mean paired difference text_ledger - credited neural_ledger (points) over eligible outcomes, clustered by conversation",
            "margin_points": margin_points,
            "clustered": primary_bound,
            "non_inferior": validity["clustered_bound_below_margin"],
            "tango_pooled_descriptive": non_inferiority_summary(elig["text_ledger"], elig["neural_ledger"], margin_points=margin_points),
        },
        "text_vs_base[eligible]": text_vs_base,
        "neural_vs_base[eligible]": _pair(elig["base"], elig["neural_ledger"]) if n_elig else None,
        "neural_vs_specificity": {
            "sign": "neural - specificity (points; positive = neural better)",
            "mean_points": spec_upper["mean"], "clustered": spec_upper,
            "upper_bound": spec_upper["upper_bound"],
            "lower_bound": (-spec_lower["upper_bound"]) if spec_lower["upper_bound"] is not None else None,
            "control_incomplete_turns": control_incomplete_turns,
            "note": "turns whose matched control could not be built for every selected span are excluded here",
        },
        "secondary_all_constraints_descriptive": {
            "accuracy": {a: _rate(v) for a, v in cells_all.items()},
            "neural_raw_vs_text": _pair(cells_all["text_ledger"], cells_all["neural_ledger"]) if cells_all["base"] else None,
            "neural_raw_vs_base": _pair(cells_all["base"], cells_all["neural_ledger"]) if cells_all["base"] else None,
            "text_vs_base": _pair(cells_all["base"], cells_all["text_ledger"]) if cells_all["base"] else None,
            "specificity_vs_base": _pair(cells_all["base"], cells_all["specificity"]) if cells_all["base"] else None,
        },
        "validity": validity,
    }
    out["primary_claim_reasons"] = [k for k, v in validity_gate.items() if not v]
    out["primary_claim_valid"] = bool(all(validity_gate.values()))
    if not validity["registered_cohort"] or not validity["complete_cohort"]:
        out["primary_claim_note"] = "incomplete or non-registered cohort: a FALSIFICATION SCREEN, not a confirmatory NI test"
    if not out["automatic"]:
        out["primary_claim_note"] = "ledger built by the HEURISTIC fallback: NOT the automatic condition"
    return out


def main():
    args = parse_args()
    sys.path.insert(0, str(ROOT / "vendor"))
    import langdetect
    langdetect.DetectorFactory.seed = 0
    from tokenizers import Tokenizer

    from stencil.bench import MAX_NEW
    from stencil.e2 import user_turn_span_records
    from stencil.e2_multiif import base_branch, is_diagnostic_key, score_turn, turn_doc
    from stencil.ledger import (
        build_ledger, context_tokens_added, generate_sustained, heuristic_is_instruction,
        is_automatic, link_entries, matched_nonledger_control, resolve_salience, select, text_ledger_context,
    )
    from stencil.obligation_gate import FIXABLE_FAMILIES

    if REGISTERED["max_new"] != MAX_NEW:
        raise RuntimeError("REGISTERED max_new drifted from stencil.bench.MAX_NEW")
    max_new = args.max_new or MAX_NEW
    data_path = ROOT / "data" / "bench" / "multiif_en.jsonl"
    model_path = ROOT / "models" / "qwen3-1.7b.pt"
    controller_path = ROOT / "results" / "qwen" / "b3-ce-s0.pt"
    base_dir = ROOT / "results" / "qwen" / "b4-multiif-base"
    manifest = json.loads((ROOT / "data" / "bench" / "pins-manifest.json").read_text())
    if sha(data_path) != manifest["converted_sha256"]["multiif_en.jsonl"]:
        raise RuntimeError("Multi-IF data provenance mismatch")
    rows = [json.loads(line) for line in data_path.read_text().splitlines()]
    if len(rows) != REGISTERED_COHORT:
        raise RuntimeError(f"registered Multi-IF cohort must contain {REGISTERED_COHORT} conversations")
    base_paths = [base_dir / f"conv-{i:03d}.json" for i in range(REGISTERED_COHORT)]
    base_records = [json.loads(p.read_text()) for p in base_paths]
    if any(r["ci"] != i for i, r in enumerate(base_records)):
        raise RuntimeError("base record order mismatch")

    sal = resolve_salience(heuristic_is_instruction if args.salience == "heuristic" else None)
    provenance = "heuristic" if args.salience == "heuristic" else sal.provenance
    note = sal.note or ("forced by --salience heuristic" if args.salience == "heuristic" else "")
    if provenance == "salience":
        segmenter = assert_real_segmenter(sal)
        segmenter_asserted = True
    else:
        segmenter, segmenter_asserted = "stencil.ledger.segment_char_spans", False
    print(f"salience provenance: {provenance} {note} segmenter={segmenter}"
          + ("" if provenance == "salience" else "  (NOT the automatic condition)"), flush=True)

    tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
    identity = cohort_identity(rows)
    todo = diagnostic_indices(rows) if args.diagnostic_only else list(range(len(rows)))
    if args.limit is not None:
        todo = todo[: args.limit]

    # CPU preflight over the SAME selection: every ledger must build and every possible
    # specificity control must construct (or be disclosed incomplete) before any GPU work.
    pre = preflight(rows, tok, sal, todo, base_records, top_k=args.top_k)
    print(f"preflight ok: {json.dumps(pre)}", flush=True)
    if args.preflight_only:
        return

    import torch
    from stencil.qwen3 import Qwen3
    from stencil.wave import WaveController

    outdir = ROOT / "results" / "qwen" / args.out
    outdir.mkdir(parents=True, exist_ok=True)
    meta = {
        "schema": 2,
        "data_sha256": sha(data_path),
        "base_records_sha256": combined_sha(base_paths),
        "model_sha256": sha(model_path),
        "controller_sha256": sha(controller_path),
        "provenance": provenance_manifest(),
        "salience_provenance": provenance,
        "salience_note": note,
        "automatic": provenance == "salience",
        "segmenter": segmenter,
        "segmenter_identity_asserted": segmenter_asserted,
        "insertable_families": sorted(FIXABLE_FAMILIES),
        "diagnostic_only": bool(args.diagnostic_only),
        "limit": args.limit,
        "registered": dict(REGISTERED),
        "registered_cohort": REGISTERED_COHORT,
        "top_k": args.top_k, "dose": args.dose, "max_new": max_new, "deadline": args.deadline,
        "margin_points": MARGIN_POINTS,
        "arms": ["base", *ARMS],
        "specificity_control": "ledger.matched_nonledger_control (width- and position-matched non-ledger spans, same dose)",
    }
    check_or_write_meta(outdir / "meta.json", meta)

    model = Qwen3()
    model.load_state_dict(torch.load(model_path, map_location="cpu"), strict=True)
    model = model.to(torch.bfloat16).cuda().eval()
    ctrl = WaveController(beta_max=1.0).cuda()
    ctrl.load_state_dict(torch.load(controller_path, map_location="cpu"))
    ctrl = ctrl.eval()

    for n_done, ci in enumerate(todo, start=1):
        row, base_record = rows[ci], base_records[ci]
        record_path = outdir / f"conv-{ci:03d}.json"
        if record_path.exists():
            continue
        turns = {}
        for turn in late_turns(row):
            context = turn_context(row, base_record, turn)
            P = len(tok.encode(context).ids)
            _, current_ids, _ = turn_doc(row, turn)
            base = base_branch(base_record, turn)
            base["per_constraint"] = [bool(x) for x in base["scores"]["inst_level_strict_acc"]]
            base["strict"] = bool(base["scores"]["prompt_level_strict_acc"])
            base["context_tokens_added"] = 0

            entries = build_ledger(tok, context, model=model, salience=sal)
            for e in entries:
                e.provenance = provenance  # honest label even when the fallback is forced
            origins = turn_origins(row, turn)
            granularity = link_entries(entries, tok, context, origins)
            aged_idx = [i for i, e in enumerate(entries) if e.turn_introduced < turn]
            aged = [entries[i] for i in aged_idx]

            # 2. text ledger: same aged entries re-appended verbatim, no bias
            text_ctx = text_ledger_context(context, aged)
            text = generate_sustained(model, tok, text_ctx, spans=[], max_new=max_new, deadline_s=args.deadline)
            text_arm = arm_branch(text, score_turn(row, turn, text.text),
                                  context_tokens_added=text.prompt_tokens - P,
                                  selected_entries=list(aged_idx))
            if text_arm["context_tokens_added"] != context_tokens_added(tok, context, text_ctx):
                raise RuntimeError(f"conv {ci} turn {turn}: text-arm token accounting disagrees")

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
            selected_idx = [entries.index(e) for e in chosen]
            neural_arm = arm_branch(neural, score_turn(row, turn, neural.text),
                                    context_tokens_added=neural.prompt_tokens - P,  # MEASURED, not a literal
                                    selected_entries=selected_idx,
                                    selected_spans=[list(s) for s in neural.spans])
            if neural_arm["context_tokens_added"] != 0:
                raise RuntimeError(f"conv {ci} turn {turn}: neural arm changed the context length")

            # 4. specificity: width- and position-matched NON-ledger spans, SAME dose
            if neural.spans:
                user_turns = [tuple(r["span"]) for r in user_turn_span_records(tok, context)]
                control, tiers = matched_nonledger_control(
                    total_len=P, selected=list(neural.spans), ledger_spans=[e.span for e in entries], user_turns=user_turns)
                control_dose = args.dose
            else:
                control, tiers, control_dose = [], [], 0.0
            control_incomplete = any(t == "none" for t in tiers)  # disclosed; excluded from neural-vs-specificity
            control_present = [s for s in control if s is not None]
            spec = generate_sustained(model, tok, context, spans=list(control_present), dose=control_dose,
                                      max_new=max_new, deadline_s=args.deadline)
            spec_arm = arm_branch(spec, score_turn(row, turn, spec.text), context_tokens_added=spec.prompt_tokens - P,
                                  control_spans=[(list(s) if s is not None else None) for s in control], control_tiers=tiers,
                                  control_dose=control_dose, control_incomplete=control_incomplete, selected_entries=[])

            constraints = constraint_rows(origins, FIXABLE_FAMILIES, selected_idx)
            turns[str(turn)] = {
                "context_sha256": hashlib.sha256(context.encode()).hexdigest(),
                "context_tokens": P,
                "instruction_ids": current_ids,
                "insertable": [iid in FIXABLE_FAMILIES for iid in current_ids],
                "constraints": constraints,
                "linkage_granularity": granularity,
                "segmenter": segmenter,
                "ledger": [e.to_record() for e in entries],
                "aged_entry_indices": aged_idx,
                "automatic": is_automatic(entries) and provenance == "salience",
                "ledger_active": any(i in aged_idx for i in selected_idx),
                "base": base,
                "arms": {"text_ledger": text_arm, "neural_ledger": neural_arm, "specificity": spec_arm},
            }
        if not turns:
            raise RuntimeError(f"conversation {ci}: no evaluable late turns")
        if sorted(turns) != identity[ci]["turns"]:
            raise RuntimeError(f"conversation {ci}: turns {sorted(turns)} != expected {identity[ci]['turns']}")
        atomic_json(record_path, {"ci": ci, "key": row["key"], "diagnostic": is_diagnostic_key(row["key"]), "turns": turns,
                                  "arms": ["base", *ARMS],  # identity + configuration ECHOED per record (sol round 2)
                                  "config": {"top_k": args.top_k, "dose": args.dose, "max_new": max_new, "deadline": args.deadline}})
        print(f"eval conversation {n_done}/{len(todo)} (ci={ci})", flush=True)

    records = [json.loads(p.read_text()) for p in sorted(outdir.glob("conv-*.json"))]
    summary = {**meta, "conversations_evaluated": len(records), "preflight": pre,
               **summarize(records, meta, cohort_size=REGISTERED_COHORT, identity=identity, margin_points=MARGIN_POINTS)}
    atomic_json(outdir / "summary.json", summary)
    print(json.dumps(summary, indent=1), flush=True)


if __name__ == "__main__":
    main()
