# ruff: noqa
"""LEDGER-KV feasibility probe (registered in LEDGER-PLAN.md, section LEDGER-KV).

Synthetic multi-turn corpus (data/b3/mt-train-300.jsonl; Multi-IF never
read). Turns 1..T-1 are generated natively (base) to build history; at the
LAST turn the prior history is EVICTED from the KV cache before query prefill and
the arms differ only in what survives:
  full                — nothing evicted (ceiling)
  evicted             — all prior turns dropped, nothing pinned
  pinned              — prior turns dropped EXCEPT aged constraint-clause K/V
  pinned_control      — exactly the same deduplicated column mass, non-constraint
  echo_only           — all prior turns dropped, with aged constraints echoed
  pinned_echo         — aged constraint-clause K/V retained, with the same echo
  full_echo           — auto focus only: nothing evicted, with the same echo
  pinned_wave_d0.5    — pinned + 0.5 pre-softmax bias on pinned columns
  pinned_wave_d1.0    — pinned + 1.0 pre-softmax bias on pinned columns
  pinned_wave_d3.0    — pinned + 3.0 pre-softmax bias on pinned columns
Scored on the last turn's AGED constraints (origin turn < last) with the
vendored checkers; degeneracy = truncation / repeated-4gram fraction.
Per-session atomic records from the first session.

``--focus oracle`` preserves the H1 marked-focus configuration. In
``--focus auto`` every arm and the salience2 DEFAULT_BACKEND finder receives
the context only after literal ``Constraint:`` labels are removed. A marked
copy exists solely to compute reported automatic-selection coverage.
"""
import argparse
import hashlib
import json
import random
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401

OPENER = "<|im_start|>assistant\n<think>\n\n</think>\n\n"
BASE_ARMS = ("full", "evicted", "pinned", "pinned_control")
ECHO_ARMS = ("echo_only", "pinned_echo")
AUTO_ECHO_ARMS = (*ECHO_ARMS, "full_echo")
DEFAULT_DOSES = (0.5, 1.0, 3.0)
DEGENERATE_REP4 = 0.5  # registered degeneracy definition: repeated-4gram frac > 0.5 OR truncated
WAVE_KILL_RULE = "degenerate sessions > 2/20 at best dose"
CHAT_CONTROL_TOKENS = ("<|im_start|>", "<|im_end|>", "<|endoftext|>")
QUOTING_RUN = 8


def dose_label(dose):
    return str(float(dose))


def arm_names(doses, *, focus="oracle"):
    echoes = AUTO_ECHO_ARMS if focus == "auto" else ECHO_ARMS
    return BASE_ARMS + echoes + tuple(f"pinned_wave_d{dose_label(dose)}" for dose in doses)


def parse_args(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--focus", choices=("auto", "oracle"), default="oracle")
    ap.add_argument("--sessions", type=int, default=20)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--max-new", type=int, default=512)
    ap.add_argument("--deadline", type=float, default=300.0)
    ap.add_argument("--dose", type=float, nargs="+", default=None)
    ap.add_argument("--out", default="ledger-kv-probe")
    ap.add_argument(
        "--eviction-timing",
        choices=("pre-query", "post-prefill"),
        default="pre-query",
    )
    args = ap.parse_args(argv)
    if args.focus == "auto" and args.dose is not None:
        ap.error("--dose is unavailable with --focus auto (H1 prime has no wave arms)")
    args.dose = list(DEFAULT_DOSES) if args.dose is None and args.focus == "oracle" else []
    return args

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def tree_sha(root):
    root = Path(root)
    files = sorted(p for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc")
    digest = hashlib.sha256()
    for path in files:
        digest.update(str(path.relative_to(root)).encode()); digest.update(b"\0")
        digest.update(path.read_bytes()); digest.update(b"\0")
    return digest.hexdigest()


def provenance_manifest():
    files = {
        "determinism.py": ROOT / "src/stencil/determinism.py",
        "tokenizer.json": ROOT / "models/qwen3-1.7b-hf/tokenizer.json",
        "bench.py": ROOT / "src/stencil/bench.py",
        "ctrb.py": ROOT / "src/stencil/ctrb.py",
        "qwen3.py": ROOT / "src/stencil/qwen3.py",
        "ledger_kv_probe.py": Path(__file__).resolve(),
        "salience2.py": ROOT / "src/stencil/salience2.py",
        "salience2_weights.json": ROOT / "src/stencil/salience2_weights.json",
        "salience2_hybrid.json": ROOT / "src/stencil/salience2_hybrid.json",
        "salience2_probe.npz": ROOT / "src/stencil/salience2_probe.npz",
    }
    out = {name: sha(path) for name, path in files.items()}
    out["vendor/ifeval"] = tree_sha(ROOT / "vendor/ifeval")
    return out


def build_meta(
    *, doses, max_new, deadline, artifact_hashes=None, focus="oracle",
    eviction_timing="pre-query",
):
    meta = {
        "schema": 3,
        "arms": list(arm_names(doses, focus=focus)),
        "doses": [float(dose) for dose in doses],
        "max_new": max_new,
        "deadline": deadline,
        "position_policy": "no_reindex_positions_continue",
        "eviction_timing": eviction_timing,
        "degenerate_def": f"truncated or rep4>{DEGENERATE_REP4}",
        "history_decode": "raw_context_greedy",
        "wave_kill_rule": WAVE_KILL_RULE,
        "provenance": provenance_manifest(),
        **(artifact_hashes or {}),
    }
    if focus == "auto":
        meta.update({
            "focus": "auto",
            "salience_backend": salience_backend(),
            "mark_isolation": (
                "all arm contexts and salience inputs have literal Constraint: markers removed; "
                "marked context is retained only for reported oracle coverage"
            ),
        })
    return meta

def atomic_json(path, value):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=1))
    tmp.rename(path)

def repeated_4gram_frac(ids):
    if len(ids) < 8:
        return 0.0
    grams = [tuple(ids[i:i + 4]) for i in range(len(ids) - 3)]
    return 1.0 - len(set(grams)) / len(grams)


def tokenized_eviction_range(tokenizer, context):
    """Tokenize ``context`` and locate its prior-history eviction range."""
    enc = tokenizer.encode(context)
    last_marker = context.rfind("<|im_start|>user\n")
    first_marker = context.find("<|im_start|>user\n")
    if first_marker < 0 or last_marker <= first_marker:
        raise ValueError("context must contain prior history and a final user turn")
    first_content = first_marker + len("<|im_start|>user\n")
    tok_first = next(i for i, (a, b) in enumerate(enc.offsets) if b > first_content)
    tok_last = next(i for i, (a, b) in enumerate(enc.offsets) if b > last_marker)
    return list(enc.ids), (tok_first, tok_last)


def current_turn_start(tokenizer, ids):
    """Return the token boundary immediately before the final user turn."""
    context = tokenizer.decode(ids, skip_special_tokens=False)
    marker = context.rfind("<|im_start|>user\n")
    if marker < 0:
        raise ValueError("current user marker missing")
    return len(tokenizer.encode(context[:marker]).ids)


def strip_constraint_marks(text):
    """Remove synthetic oracle labels before automatic selection or generation."""
    return text.replace("Constraint:", "")


def salience_backend():
    from stencil.salience2 import DEFAULT_BACKEND

    return DEFAULT_BACKEND


def _user_turns(context):
    marker = "<|im_start|>user\n"
    turns = []
    cursor = 0
    while True:
        marker_start = context.find(marker, cursor)
        if marker_start < 0:
            return turns
        start = marker_start + len(marker)
        end = context.find("<|im_end|>", start)
        if end < 0:
            raise ValueError("unterminated user turn")
        turns.append((start, end))
        cursor = end + 1


def _token_span(enc, start, end, *, contained=False):
    if contained:
        # Include the tokenizer's leading-space token at the clause start, but
        # never the token that crosses the clause end (the H1 bleed bug).
        tokens = [i for i, (a, b) in enumerate(enc.offsets) if a < end and b > start and b <= end]
    else:
        tokens = [i for i, (a, b) in enumerate(enc.offsets) if a < end and b > start]
    return (tokens[0], tokens[-1] + 1) if tokens else None


def _oracle_char_records(context, last_turn):
    """Oracle clauses for measurement, bounded before the next mark/reminder."""
    reminder = "Every earlier constraint from this conversation still applies to this reply as well."
    records = []
    for turn, (user_start, user_end) in enumerate(_user_turns(context), start=1):
        cursor = user_start
        while True:
            mark = context.find("Constraint:", cursor, user_end)
            if mark < 0:
                break
            start = mark + len("Constraint:")
            next_mark = context.find("Constraint:", start, user_end)
            reminder_start = context.find(reminder, start, user_end)
            candidates = [user_end]
            candidates.extend(x for x in (next_mark, reminder_start) if x >= 0)
            end = min(candidates)
            while start < end and context[start].isspace():
                start += 1
            while end > start and context[end - 1].isspace():
                end -= 1
            records.append({"char_span": (start, end), "origin_turn": turn,
                            "is_aged": turn < last_turn})
            cursor = mark + 1
    return records


def oracle_focus_records(tokenizer, context, *, last_turn):
    enc = tokenizer.encode(context)
    records = []
    for record in _oracle_char_records(context, last_turn):
        span = _token_span(enc, *record["char_span"], contained=True)
        if span is not None:
            records.append({**record, "span": span})
    return records


def focus_span_records(tokenizer, context, *, last_turn, focus, finder=None,
                       marked_span_reader=None):
    """Select aged focus spans; auto never invokes the oracle-mark reader."""
    if focus == "oracle":
        if marked_span_reader is None:
            from stencil.e2 import constraint_span_records

            records = constraint_span_records(tokenizer, context)
        else:
            records = marked_span_reader(tokenizer, context)
        return [r for r in records if r["origin_turn"] < last_turn]
    if "Constraint:" in context:
        raise AssertionError("automatic focus context still contains oracle marks")
    if finder is None:
        from stencil.salience2 import extract_instructions

        finder = extract_instructions
    enc = tokenizer.encode(context)
    records = []
    for turn, (start, end) in enumerate(_user_turns(context), start=1):
        content = context[start:end]
        for found in finder(content, backend=salience_backend()):
            span = _token_span(enc, start + found.start, start + found.end, contained=True)
            if span is not None and turn < last_turn:
                records.append({"span": span, "origin_turn": turn, "is_aged": True})
    return records


def auto_selection_metrics(tokenizer, marked_context, unmarked_context, selected, *, last_turn):
    """Coverage of oracle clauses in unmarked token coordinates, plus false extras."""
    if strip_constraint_marks(marked_context) != unmarked_context:
        raise AssertionError("unmarked context is not the mark-stripped oracle context")
    enc = tokenizer.encode(unmarked_context)
    oracle = []
    for record in _oracle_char_records(marked_context, last_turn):
        if not record["is_aged"]:
            continue
        start, end = record["char_span"]
        start -= marked_context[:start].count("Constraint:") * len("Constraint:")
        end -= marked_context[:end].count("Constraint:") * len("Constraint:")
        span = _token_span(enc, start, end, contained=False)
        if span is not None:
            oracle.append(set(range(*span)))
    picked = [set(range(*record["span"])) for record in selected]
    covered = sum(any(len(gold & pred) / len(gold) >= 0.5 for pred in picked) for gold in oracle)
    extra = sum(not any(pred & gold for gold in oracle) for pred in picked)
    return {
        "auto_coverage": covered / len(oracle) if oracle else 0.0,
        "auto_extra": extra,
    }


def echo_context(tokenizer, context, aged_records):
    """Render aged spans, clamped before a next mark or reminder sentence."""
    from stencil.ledger import Entry, render_text_ledger, text_ledger_context

    enc = tokenizer.encode(context)
    ids = enc.ids
    entries = []
    for record in aged_records:
        start, end = record["span"]
        if not 0 <= start < end <= len(ids):
            raise ValueError("aged constraint span outside context")
        char_start = enc.offsets[start][0]
        char_end = enc.offsets[end - 1][1]
        window = context[char_start:char_end]
        cuts = [
            pos for pos in (
                window.find(" Constraint:", 1),
                window.find("Every earlier constraint from this conversation still applies", 1),
            ) if pos >= 0
        ]
        if window.rstrip().endswith(" Constraint"):
            cuts.append(window.rfind(" Constraint"))
        if cuts:
            bounded = _token_span(enc, char_start, char_start + min(cuts), contained=True)
            if bounded is None:
                raise ValueError("constraint span is empty at its clause boundary")
            start, end = bounded
        span_text = tokenizer.decode(ids[start:end], skip_special_tokens=False)
        if any(token in span_text for token in CHAT_CONTROL_TOKENS):
            raise ValueError("chat-control token inside echoed text")
        entries.append(Entry(span_text, (start, end), None, int(record["origin_turn"])))
    rendered = render_text_ledger(entries)
    echoed = text_ledger_context(context, entries)
    cut = context.rfind("<|im_end|>")
    if rendered and echoed != context[:cut] + "\n\n" + rendered + context[cut:]:
        raise AssertionError("echo did not land before the final user <|im_end|>")
    return echoed, entries, rendered


def invalid_output(text):
    """Registered empty/non-text/chat-token generation check."""
    return (not text or not any(ch.isalnum() for ch in text)
            or any(token in text for token in CHAT_CONTROL_TOKENS))


def detect_quoting(response_ids, echo_ids, *, echo_arm):
    """Whether a response contains eight consecutive tokens from the echo."""
    if not echo_arm or len(response_ids) < QUOTING_RUN or len(echo_ids) < QUOTING_RUN:
        return False
    echo_windows = {
        tuple(echo_ids[i:i + QUOTING_RUN])
        for i in range(len(echo_ids) - QUOTING_RUN + 1)
    }
    return any(
        tuple(response_ids[i:i + QUOTING_RUN]) in echo_windows
        for i in range(len(response_ids) - QUOTING_RUN + 1)
    )

def matched_control_spans(keep, evict_range):
    """Position-match exactly the deduplicated surviving-column mass."""
    lo, hi = evict_range
    pinned = {column for start, end in keep for column in range(max(lo, start), min(hi, end))}
    available = set(range(lo, hi)) - pinned
    if len(available) < len(pinned):
        raise RuntimeError(f"cannot match {len(pinned)} pinned columns with only {len(available)} controls")
    chosen = set()
    for target in sorted(pinned):
        candidate = min(available, key=lambda col: (abs(col - target), col < target, col))
        chosen.add(candidate)
        available.remove(candidate)
    ordered = sorted(chosen)
    spans = []
    for column in ordered:
        if spans and spans[-1][1] == column:
            spans[-1] = (spans[-1][0], column + 1)
        else:
            spans.append((column, column + 1))
    assert len({i for start, end in spans for i in range(start, end)}) == len(pinned)
    return spans


def is_degenerate(g):
    return bool(g["truncated"] or g["rep4"] > DEGENERATE_REP4)


def run_arm(m, tok, ids, arm, keep, evict_range, dose, max_new, deadline_s,
            control_keep=(), eviction_timing="pre-query", deficit_spans=(),
            deficit_tau=None):
    import torch

    from stencil.bench import EOS, WAVE_LAYERS
    from stencil.qwen3 import KVCache, prefill_with_eviction
    device = next(m.parameters()).device
    cache = KVCache(m.cfg)
    out = []
    t0 = time.monotonic()
    timed_out = False
    with torch.no_grad():
        cols = []
        pins = ()
        if arm not in ("full", "full_echo"):
            pins = (
                () if arm in ("evicted", "echo_only")
                else control_keep if arm == "pinned_control"
                else keep
            )
        logits, imap, _, _ = prefill_with_eviction(
            m,
            cache,
            torch.tensor([ids], device=device),
            history_end=(
                evict_range[1]
                if evict_range is not None
                else current_turn_start(tok, ids)
            ),
            evict_range=None if arm in ("full", "full_echo") else evict_range,
            keep=pins,
            eviction_timing=eviction_timing,
        )
        if arm not in ("full", "full_echo"):
            cols = sorted({imap[o] for s, e in pins for o in range(s, e) if o in imap})
        mapped_deficits = [
            (sorted({imap[o] for o in range(*span) if o in imap}), cap)
            for span, cap in deficit_spans
        ]
        mapped_deficits = [item for item in mapped_deficits if item[0] and item[1] > 0.0]
        nxt = int(logits[0, -1].argmax())
        while nxt not in EOS and len(out) < max_new:
            if time.monotonic() - t0 > deadline_s:
                timed_out = True
                break
            out.append(nxt)
            ab = None
            if arm.startswith("pinned_wave_d") and cols:
                row = torch.zeros(1, cache.k[0].shape[2] + 1, device=device)
                row[0, cols] = dose
                ab = {L: row for L in WAVE_LAYERS}
            deficit_hook = None
            if mapped_deficits:
                if deficit_tau is None:
                    raise ValueError("deficit_tau is required with deficit_spans")
                gates = {}
                for layer in WAVE_LAYERS:
                    layer_gates = []
                    for span_cols, cap in mapped_deficits:
                        mask = torch.zeros(
                            cache.k[0].shape[2] + 1,
                            dtype=torch.bool,
                            device=device,
                        )
                        mask[span_cols] = True
                        layer_gates.append((mask, deficit_tau, cap))
                    gates[layer] = layer_gates
                deficit_hook = (min(WAVE_LAYERS), lambda _hidden: gates)
            logits = m(
                torch.tensor([[nxt]], device=device),
                cache=cache,
                attn_bias=ab,
                deficit_hook=deficit_hook,
            )
            nxt = int(logits[0, -1].argmax())
    text = tok.decode(out, skip_special_tokens=False)
    return {
        "text": text, "n": len(out),
        "truncated": len(out) >= max_new,
        "timed_out": timed_out, "rep4": repeated_4gram_frac(out),
        "invalid_output": invalid_output(text),
        "generated_token_ids": list(out),
        "pinned_cols": len(cols), "cache_cols": int(cache.k[0].shape[2]),
    }


def session_record(*, session, key, topic, n_turns, evict_range, keep, control_keep,
                   n_aged, history_token_ids, context_token_ids, arms,
                   echo_context_token_ids=(), echo_tokens_added=0, echo_text_sha256="",
                   auto_coverage=None, auto_extra=None):
    pinned_columns = {i for start, end in keep for i in range(start, end)}
    control_columns = {i for start, end in control_keep for i in range(start, end)}
    if len(control_columns) != len(pinned_columns):
        raise AssertionError(
            f"pinned_control column mismatch: {len(control_columns)} != {len(pinned_columns)}"
        )
    if control_columns & pinned_columns:
        raise AssertionError("pinned_control overlaps pinned constraint columns")
    record = {
        "session": session,
        "key": key,
        "topic": topic,
        "n_turns": n_turns,
        "evict_range": list(evict_range),
        "keep": [list(span) for span in keep],
        "control_keep": [list(span) for span in control_keep],
        "n_aged": n_aged,
        "history_token_ids": list(history_token_ids),
        "context_token_ids": list(context_token_ids),
        "echo_context_token_ids": list(echo_context_token_ids),
        "echo_tokens_added": int(echo_tokens_added),
        "echo_text_sha256": echo_text_sha256,
        "arms": arms,
    }
    if any("generated_token_ids" not in branch for branch in arms.values()):
        raise AssertionError("every arm must record generated_token_ids")
    if any(not isinstance(branch.get("quoting"), bool) for branch in arms.values()):
        raise AssertionError("every arm must record quoting as a bool")
    if auto_coverage is not None:
        record["auto_coverage"] = float(auto_coverage)
        record["auto_extra"] = int(auto_extra)
    return record


def _percentile(sorted_values, q):
    if not sorted_values:
        return None
    index = (len(sorted_values) - 1) * q
    lower = int(index)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = index - lower
    return sorted_values[lower] * (1.0 - weight) + sorted_values[upper] * weight


def paired_bootstrap_pinned_minus_control(records, *, n_resamples=2000, seed=0):
    """Session-paired percentile bootstrap of pinned minus exact control."""
    diffs = []
    for record in records:
        n = record["arms"]["pinned"]["aged_n"]
        pinned = record["arms"]["pinned"]["scores"][:n]
        control = record["arms"]["pinned_control"]["scores"][:n]
        if len(pinned) != len(control) or not pinned:
            raise ValueError("paired non-empty aged score vectors required")
        diffs.append(sum(float(a) - float(b) for a, b in zip(pinned, control, strict=True)) / len(pinned))
    if not diffs:
        return {"mean": None, "lower": None, "upper": None, "n_sessions": 0,
                "confidence": 0.95, "resamples": n_resamples, "seed": seed}
    rng = random.Random(seed)
    draws = sorted(sum(diffs[rng.randrange(len(diffs))] for _ in diffs) / len(diffs)
                   for _ in range(n_resamples))
    return {
        "mean": sum(diffs) / len(diffs),
        "lower": _percentile(draws, 0.025),
        "upper": _percentile(draws, 0.975),
        "n_sessions": len(diffs),
        "confidence": 0.95,
        "resamples": n_resamples,
        "seed": seed,
        "unit": "session",
    }


def summarize_records(records, arms_registered, meta=None):
    """Aggregate arm metrics and registered H1 pass-count contrasts."""
    summ = {**(meta or {}), "sessions": len(records)}
    for arm in arms_registered:
        passed = sum(r["arms"][arm]["aged_pass"] for r in records)
        total = sum(r["arms"][arm]["aged_n"] for r in records)
        nonquoting = [r for r in records if not r["arms"][arm]["quoting"]]
        nonquoting_passed = sum(r["arms"][arm]["aged_pass"] for r in nonquoting)
        nonquoting_total = sum(r["arms"][arm]["aged_n"] for r in nonquoting)
        summ[arm] = {
            "aged_pass": passed,
            "aged_n": total,
            "rate": passed / max(1, total),
            "trunc": sum(r["arms"][arm]["truncated"] for r in records),
            "timeout": sum(r["arms"][arm]["timed_out"] for r in records),
            "mean_rep4": sum(r["arms"][arm]["rep4"] for r in records) / max(1, len(records)),
            "degenerate": sum(is_degenerate(r["arms"][arm]) for r in records),
            "invalid_output": sum(
                r["arms"][arm].get("invalid_output", invalid_output(r["arms"][arm].get("text", "ok")))
                for r in records
            ),
            "quoting_rate": sum(r["arms"][arm]["quoting"] for r in records) / max(1, len(records)),
            "pass_rate_quoting_excluded": nonquoting_passed / nonquoting_total if nonquoting_total else None,
        }

    gap_passes = summ["full"]["aged_pass"] - summ["evicted"]["aged_pass"]
    summ["gap_full_minus_evicted_passes"] = gap_passes
    contrast_arms = (
        ("pinned_minus_evicted", "pinned", "evicted"),
        ("echo_only_minus_evicted", "echo_only", "evicted"),
        ("pinned_echo_minus_echo_only", "pinned_echo", "echo_only"),
        ("pinned_minus_pinned_control", "pinned", "pinned_control"),
    )
    if "full_echo" in arms_registered:
        contrast_arms += (("full_echo_minus_full", "full_echo", "full"),)
    summ["contrasts"] = {}
    for label, treatment, reference in contrast_arms:
        difference = summ[treatment]["aged_pass"] - summ[reference]["aged_pass"]
        summ["contrasts"][label] = {
            "pass_count_difference": difference,
            "recovered_fraction_of_gap": difference / gap_passes if gap_passes > 0 else None,
        }
    full = summ["full"]
    summ["safety_table"] = {}
    for arm in arms_registered:
        values = {
            "timeouts": (summ[arm]["timeout"], full["timeout"], summ[arm]["timeout"] == 0),
            "truncations": (summ[arm]["trunc"], full["trunc"], summ[arm]["trunc"] <= full["trunc"] + 1),
            "degenerate_sessions": (
                summ[arm]["degenerate"], full["degenerate"],
                summ[arm]["degenerate"] <= full["degenerate"],
            ),
            "invalid_output": (
                summ[arm]["invalid_output"], full["invalid_output"],
                summ[arm]["invalid_output"] <= full["invalid_output"],
            ),
        }
        table = {
            name: {"events": count, "vs_full": count - baseline, "safe": safe}
            for name, (count, baseline, safe) in values.items()
        }
        table["safe"] = all(item[2] for item in values.values())
        summ["safety_table"][arm] = table
    if records and all("auto_coverage" in record for record in records):
        summ["automatic_selection"] = {
            "mean_coverage": sum(r["auto_coverage"] for r in records) / len(records),
            "total_extra": sum(r["auto_extra"] for r in records),
            "per_session": [
                {"session": r["session"], "auto_coverage": r["auto_coverage"],
                 "auto_extra": r["auto_extra"]}
                for r in records
            ],
        }
    return summ

def main():
    determinism.assert_gpu_free_or_owned()
    args = parse_args()
    import torch
    from tokenizers import Tokenizer

    from stencil.causal_moments import score_row_constraints
    from stencil.qwen3 import Qwen3

    data_path = ROOT / "data" / "b3" / "mt-train-300.jsonl"
    model_path = ROOT / "models" / "qwen3-1.7b.pt"
    sessions = [json.loads(l) for l in data_path.read_text().splitlines()][args.start:args.start + args.sessions]
    outdir = ROOT / "results" / "qwen" / args.out
    outdir.mkdir(parents=True, exist_ok=True)
    doses = tuple(args.dose)
    arms_registered = arm_names(doses, focus=args.focus)
    meta = build_meta(
        doses=doses,
        max_new=args.max_new,
        deadline=args.deadline,
        focus=args.focus,
        eviction_timing=args.eviction_timing,
        artifact_hashes={
            "corpus": str(data_path.relative_to(ROOT)),
            "corpus_sha256": sha(data_path),
            "model_sha256": sha(model_path),
            "qwen3_sha256": sha(ROOT / "src/stencil/qwen3.py"),
        },
    )
    mp = outdir / "meta.json"
    if mp.exists():
        if json.loads(mp.read_text()) != meta:
            raise RuntimeError("resume provenance mismatch")
    else:
        atomic_json(mp, meta)

    tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
    m = Qwen3()
    m.load_state_dict(torch.load(model_path, map_location="cpu"), strict=True)
    m = m.to(torch.bfloat16).cuda().eval()

    for si, sess in enumerate(sessions, start=args.start):
        rp = outdir / f"session-{si:03d}.json"
        if rp.exists():
            continue
        turns = sess["turns"]
        history = ""
        marked_history = ""
        for turn in turns[:-1]:
            prompt = strip_constraint_marks(turn["prompt"]) if args.focus == "auto" else turn["prompt"]
            ctx = history + f"<|im_start|>user\n{prompt}<|im_end|>\n" + OPENER
            # verifier (2026-09-01): generate_cached wraps in TMPL -> double
            # scaffold; decode the raw context instead
            g = run_arm(m, tok, tok.encode(ctx).ids, "full", [], None, 0.0, args.max_new, args.deadline)
            text = g["text"]
            history += f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n{text}<|im_end|>\n"
            marked_history += (
                f"<|im_start|>user\n{turn['prompt']}<|im_end|>\n"
                f"<|im_start|>assistant\n{text}<|im_end|>\n"
            )
        last = turns[-1]
        history_ids = tok.encode(history).ids
        last_prompt = strip_constraint_marks(last["prompt"]) if args.focus == "auto" else last["prompt"]
        context = history + f"<|im_start|>user\n{last_prompt}<|im_end|>\n" + OPENER
        marked_context = (
            marked_history + f"<|im_start|>user\n{last['prompt']}<|im_end|>\n" + OPENER
            if args.focus == "auto" else context
        )
        if args.focus == "auto" and ("Constraint:" in context or strip_constraint_marks(marked_context) != context):
            raise AssertionError("automatic arm context is not exactly the mark-stripped context")
        ids, evict_range = tokenized_eviction_range(tok, context)
        T_last = len(turns)
        aged_recs = focus_span_records(tok, context, last_turn=T_last, focus=args.focus)
        keep = [tuple(r["span"]) for r in aged_recs]
        echoed_context, _, echo_text = echo_context(tok, context, aged_recs)
        echo_ids, echo_evict_range = tokenized_eviction_range(tok, echoed_context)
        if tok.decode(ids[slice(*evict_range)]) != tok.decode(echo_ids[slice(*echo_evict_range)]):
            raise AssertionError("echo tokenization changed the prior-history eviction text")
        echo_keep = keep
        echo_token_ids = tok.encode(echo_text).ids
        echo_tokens_added = len(echo_ids) - len(ids)
        echo_text_sha256 = hashlib.sha256(echo_text.encode()).hexdigest()
        control_keep = matched_control_spans(keep, evict_range)
        pinned_count = len({i for start, end in keep for i in range(start, end)})
        control_count = len({i for start, end in control_keep for i in range(start, end)})
        assert control_count == pinned_count, f"session {si}: control {control_count} != pinned {pinned_count}"
        row = {"key": int(sess["key"]) * 10 + T_last,
               "instruction_id_list": last["instruction_id_list"], "kwargs": last["kwargs"]}
        # aged constraints = those whose clause originates in an earlier turn;
        # map by order: the corpus lists are cumulative in introduction order
        oracle_recs = oracle_focus_records(tok, marked_context, last_turn=T_last)
        n_aged = sum(r["is_aged"] for r in oracle_recs)
        selection_metrics = (
            auto_selection_metrics(tok, marked_context, context, aged_recs, last_turn=T_last)
            if args.focus == "auto" else {}
        )
        arms = {}
        for arm in arms_registered:
            dose = float(arm.rsplit("_d", 1)[1]) if arm.startswith("pinned_wave_d") else 0.0
            is_echo = arm in AUTO_ECHO_ARMS
            arm_ids = echo_ids if is_echo else ids
            arm_keep = echo_keep if is_echo else keep
            arm_evict_range = echo_evict_range if is_echo else evict_range
            g = run_arm(
                m, tok, arm_ids, arm, arm_keep, arm_evict_range, dose,
                args.max_new, args.deadline, control_keep=control_keep,
                eviction_timing=args.eviction_timing,
            )
            g["degenerate"] = is_degenerate(g)
            scores = score_row_constraints(row, g["text"])
            g["scores"] = list(scores)
            g["aged_pass"] = sum(scores[:n_aged])
            g["aged_n"] = n_aged
            g["quoting"] = detect_quoting(
                g["generated_token_ids"], echo_token_ids, echo_arm=is_echo
            )
            g["invalid_output"] = invalid_output(g["text"])
            arms[arm] = g
        assert arms["pinned"]["pinned_cols"] == arms["pinned_control"]["pinned_cols"]
        rec = session_record(
            session=si, key=sess["key"], topic=sess["topic"], n_turns=T_last,
            evict_range=evict_range, keep=keep, control_keep=control_keep, n_aged=n_aged,
            history_token_ids=history_ids, context_token_ids=ids, arms=arms,
            echo_context_token_ids=echo_ids, echo_tokens_added=echo_tokens_added,
            echo_text_sha256=echo_text_sha256,
            **selection_metrics,
        )
        rec["context_tokens"] = len(ids)
        atomic_json(rp, rec)
        print(f"session {si} aged={n_aged} " + " ".join(f"{a}={arms[a]['aged_pass']}/{n_aged}(rep4={arms[a]['rep4']:.2f},n={arms[a]['n']})" for a in arms_registered), flush=True)

    records = [json.loads(p.read_text()) for p in sorted(outdir.glob("session-*.json"))]
    summ = summarize_records(records, arms_registered, meta)
    gap = summ["full"]["rate"] - summ["evicted"]["rate"]
    summ["gap_full_minus_evicted"] = gap
    summ["recovered_frac_pinned"] = (summ["pinned"]["rate"] - summ["evicted"]["rate"]) / gap if gap > 0 else None
    wave_arms = [a for a in arms_registered if a.startswith("pinned_wave_d")]
    if wave_arms:
        best_wave = max(wave_arms, key=lambda a: (summ[a]["rate"], -summ[a]["degenerate"]))
        summ["wave_best_dose_arm"] = best_wave
        summ["wave_killed"] = summ[best_wave]["degenerate"] > 2
        summ["recovered_frac_pinned_wave_best_dose"] = (summ[best_wave]["rate"] - summ["evicted"]["rate"]) / gap if gap > 0 else None
    summ["paired_bootstrap_pinned_minus_control"] = paired_bootstrap_pinned_minus_control(records)
    atomic_json(outdir / "summary.json", summ)
    print(json.dumps({k: v for k, v in summ.items() if k in arms_registered or k.startswith(("gap", "recovered", "paired", "wave_"))}, indent=1))

if __name__ == "__main__":
    main()
