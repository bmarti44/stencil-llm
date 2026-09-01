"""Pure E2 harvest and evaluation helpers.

The helpers here deliberately contain no model loading or generation.  That
keeps the corrected span, sampling, arm, and artifact contracts independently
testable and makes importing the harvest runner side-effect free.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence

NOMINAL_ARM = "sustained_all"


def user_turn_span_records(tokenizer, context: str) -> list[dict]:
    """Automatic, marker-free user-turn spans shared by train and deploy."""
    marker = "<|im_start|>user\n"
    enc = tokenizer.encode(context)
    turns = []
    cursor = 0
    while True:
        marker_start = context.find(marker, cursor)
        if marker_start < 0:
            break
        content_start = marker_start + len(marker)
        content_end = context.find("<|im_end|>", content_start)
        if content_end < 0:
            raise ValueError("unterminated user turn")
        turns.append((content_start, content_end))
        cursor = content_end + 1
    current_turn = len(turns)
    records = []
    for index, (start, end) in enumerate(turns, start=1):
        tokens = [
            i for i, (a, b) in enumerate(enc.offsets) if a < end and b > start
        ]
        if not tokens:
            raise ValueError(f"user turn {index} has no tokens")
        records.append(
            {
                "span": (tokens[0], tokens[-1] + 1),
                "origin_turn": index,
                "is_aged": index < current_turn,
            }
        )
    return records


def constraint_span_records(tokenizer, context: str) -> list[dict]:
    """Return bounded constraint spans with one-based user-turn origins."""
    enc = tokenizer.encode(context)
    user_starts: list[int] = []
    cursor = 0
    while True:
        pos = context.find("<|im_start|>user", cursor)
        if pos < 0:
            break
        user_starts.append(pos)
        cursor = pos + 1
    if not user_starts:
        return []

    current_turn = len(user_starts)
    records: list[dict] = []
    cursor = 0
    while True:
        start = context.find("Constraint:", cursor)
        if start < 0:
            break
        enclosing = [i for i, pos in enumerate(user_starts) if pos <= start]
        if not enclosing:
            cursor = start + 1
            continue
        origin = enclosing[-1] + 1
        next_constraint = context.find("Constraint:", start + 1)
        user_end = context.find("<|im_end|>", start)
        ends = [x for x in (next_constraint, user_end) if x >= 0]
        end = min(ends) if ends else len(context)
        token_indices = [
            i for i, (a, b) in enumerate(enc.offsets) if a < end and b > start
        ]
        if token_indices:
            records.append(
                {
                    "span": (token_indices[0], token_indices[-1] + 1),
                    "origin_turn": origin,
                    "is_aged": origin < current_turn,
                }
            )
        cursor = start + 1
    return records


def select_candidate_records(
    trace: Sequence[Mapping], *, top_k: int = 4, temporal_k: int = 4
) -> list[dict]:
    """Fixed union of conflict-ranked and evenly spaced eligible moments."""
    eligible = [dict(r) for r in trace if r.get("features") is not None]
    if not eligible:
        return []
    chronological = sorted(eligible, key=lambda r: int(r["step"]))
    ranked = sorted(
        eligible,
        key=lambda r: (-float(r["features"][0]), int(r["step"])),
    )[: max(0, top_k)]
    if temporal_k <= 0:
        temporal = []
    elif temporal_k == 1:
        temporal = [chronological[len(chronological) // 2]]
    else:
        indices = {
            round(i * (len(chronological) - 1) / (temporal_k - 1))
            for i in range(temporal_k)
        }
        temporal = [chronological[i] for i in sorted(indices)]
    by_step = {int(r["step"]): r for r in ranked + temporal}
    return [by_step[s] for s in sorted(by_step)]


def matched_nonconstraint_spans(
    *, total_len: int, spans: Sequence[tuple[int, int]], width: int
) -> tuple[tuple[int, int], ...]:
    """Take exactly ``width`` deterministic tokens outside constraint spans."""
    if total_len < 0 or width < 0:
        raise ValueError("lengths must be nonnegative")
    blocked = [False] * total_len
    for a, b in spans:
        if not (0 <= a < b <= total_len):
            raise ValueError("constraint span outside context")
        blocked[a:b] = [True] * (b - a)
    if sum(not x for x in blocked) < width:
        raise ValueError("insufficient non-constraint tokens for matched control")

    # Work backward so the control is near the active turn while still being
    # disjoint from every constraint.  Coalesce adjacent chosen tokens.
    chosen = sorted(i for i in range(total_len - 1, -1, -1) if not blocked[i])[-width:]
    if width == 0:
        return ()
    runs: list[list[int]] = []
    for i in chosen:
        if not runs or i != runs[-1][-1] + 1:
            runs.append([i])
        else:
            runs[-1].append(i)
    return tuple((r[0], r[-1] + 1) for r in runs)


def mass_matched_nonconstraint_control(
    *,
    total_len: int,
    spans: Sequence[tuple[int, int]],
    target_dose: float,
) -> tuple[tuple[tuple[int, int], ...], float]:
    """Disjoint complement with dose scaled to equal target logit-bias mass."""
    blocked = set()
    for a, b in spans:
        if not 0 <= a < b <= total_len:
            raise ValueError("constraint span outside context")
        blocked.update(range(a, b))
    available = total_len - len(blocked)
    if available <= 0:
        raise ValueError("no non-constraint control tokens")
    control = matched_nonconstraint_spans(
        total_len=total_len, spans=spans, width=available
    )
    target_width = len(blocked)
    return control, float(target_dose) * target_width / available


def arm_specs(
    spans: Sequence[tuple[int, int]],
    *,
    selected_span: int,
    aged_indices: Sequence[int],
    control_spans: Sequence[tuple[int, int]],
    control_dose: float = 3.0,
) -> dict[str, dict]:
    """The Opus-validated dose/duration arm table, frozen pre-harvest."""
    all_spans = tuple(tuple(x) for x in spans)
    if not (0 <= selected_span < len(all_spans)):
        raise ValueError("selected span index out of range")
    aged = tuple(all_spans[i] for i in aged_indices)
    if not aged:
        aged = (all_spans[0],)
    return {
        "registered": {
            "spans": (all_spans[selected_span],),
            "dose": 1.0,
            "burst_tokens": 4,
        },
        "sustained_all": {
            "spans": all_spans,
            "dose": 3.0,
            "burst_tokens": 10**6,
        },
        "sustained_aged": {
            "spans": aged,
            "dose": 3.0,
            "burst_tokens": 10**6,
        },
        "control": {
            "spans": tuple(tuple(x) for x in control_spans),
            "dose": float(control_dose),
            "burst_tokens": 10**6,
        },
    }


def classify_utility(native_scores: Sequence[bool], arm_scores: Sequence[bool]):
    if len(native_scores) != len(arm_scores):
        raise ValueError("branch score width changed")
    delta = sum(bool(x) for x in arm_scores) - sum(bool(x) for x in native_scores)
    return ("helpful" if delta > 0 else "harmful" if delta < 0 else "neutral"), delta


def make_branch_record(
    response: str,
    scores: Sequence[bool],
    n_generated: int,
    truncated: bool,
    timed_out: bool,
) -> dict:
    if not isinstance(response, str):
        raise TypeError("response must be text")
    return {
        "scores": [bool(x) for x in scores],
        "n_pass": sum(bool(x) for x in scores),
        "n_generated": int(n_generated),
        "truncated": bool(truncated),
        "timed_out": bool(timed_out),
        "response_sha256": hashlib.sha256(response.encode()).hexdigest(),
        "response": response,
    }


def make_moment_record(
    *,
    session: int,
    turn: int,
    step: int,
    features: Sequence[float],
    response_position: float,
    selected_span: int,
    selected_origin: int,
    topic: str,
    changed_family: Sequence[str],
    native: Mapping,
    arms: Mapping[str, Mapping],
) -> dict:
    if len(features) != 6 or not arms or NOMINAL_ARM not in arms:
        raise ValueError("non-vacuous six-feature nominal-arm record required")
    native_scores = native["scores"]
    arm_records: dict[str, dict] = {}
    for name, branch in arms.items():
        item = dict(branch)
        label, delta = classify_utility(native_scores, item["scores"])
        item["label_vs_native"] = label
        item["utility_delta"] = delta
        arm_records[name] = item
    label = arm_records[NOMINAL_ARM]["label_vs_native"]
    delta = arm_records[NOMINAL_ARM]["utility_delta"]
    return {
        "session": int(session),
        "turn": int(turn),
        "step": int(step),
        "features": [float(x) for x in features],
        "response_position": float(response_position),
        "selected_span": int(selected_span),
        "selected_origin": int(selected_origin),
        "topic": str(topic),
        "changed_family": list(changed_family),
        "label": label,
        "utility_delta": delta,
        "native": dict(native),
        "arms": arm_records,
    }


def summarize_oracle_records(records: Sequence[Mapping], arms: Sequence[str]) -> dict:
    """Aggregate oracle trials by deriving each arm's per-session best.

    Trial records are the source of truth.  There is intentionally no
    dependency on a separately cached ``by_arm`` field.
    """
    constraints = sum(int(r["n_constraints"]) for r in records)
    if not records or constraints <= 0:
        raise ValueError("nonempty oracle records with constraints required")
    native_pass = sum(int(r["native_pass"]) for r in records)
    oracle_pass = sum(int(r["oracle_best_pass"]) for r in records)
    by_arm = {}
    for arm in arms:
        total = 0
        for rec in records:
            trials = [
                int(t["n_pass"])
                for t in rec.get("trials", ())
                if t.get("arm") == arm
            ]
            total += max(trials, default=int(rec["native_pass"]))
        by_arm[str(arm)] = total / constraints
    native_rate = native_pass / constraints
    oracle_rate = oracle_pass / constraints
    return {
        "sessions": len(records),
        "constraints": constraints,
        "native_pass_rate": native_rate,
        "oracle_pass_rate": oracle_rate,
        "sessions_with_any_oracle_gain": sum(
            int(r.get("oracle_gain", 0)) > 0 for r in records
        ),
        "total_trials": sum(len(r.get("trials", ())) for r in records),
        "oracle_ceiling_pts": (oracle_rate - native_rate) * 100.0,
        "by_arm_pass_rate": by_arm,
    }
