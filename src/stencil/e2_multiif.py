"""Pure Multi-IF replay construction and registered E2 endpoint analysis."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from collections.abc import Mapping, Sequence

from stencil.e2_stats import mcnemar_one_sided

OPENER = "<|im_start|>assistant\n<think>\n\n</think>\n\n"


def is_diagnostic_key(key: str) -> bool:
    return int(hashlib.sha256(str(key).encode()).hexdigest(), 16) % 9 == 0


def build_replay_context(
    prompts: Sequence[str],
    base_responses: Sequence[str],
    *,
    turn: int,
    positive_control: bool,
) -> str:
    if not 1 <= turn <= len(prompts) or len(base_responses) < turn - 1:
        raise ValueError("invalid replay turn/history")
    history = ""
    for i in range(turn - 1):
        history += f"<|im_start|>user\n{prompts[i]}<|im_end|>\n"
        history += f"<|im_start|>assistant\n{base_responses[i]}<|im_end|>\n"
    current = prompts[turn - 1]
    if positive_control and turn > 1:
        restated = "\n\nEarlier user instructions restated verbatim:\n" + "\n\n".join(
            prompts[: turn - 1]
        )
        current += restated
    return history + f"<|im_start|>user\n{current}<|im_end|>\n" + OPENER


def paired_endpoint(pairs: Sequence[tuple[bool, bool]]) -> dict:
    if not pairs:
        raise ValueError("paired observations required")
    base_pass = sum(bool(base) for base, _ in pairs)
    arm_pass = sum(bool(arm) for _, arm in pairs)
    repairs = sum(not base and arm for base, arm in pairs)
    regressions = sum(base and not arm for base, arm in pairs)
    return {
        "n": len(pairs),
        "base_pass": base_pass,
        "arm_pass": arm_pass,
        "base_rate": base_pass / len(pairs),
        "arm_rate": arm_pass / len(pairs),
        "delta_points": (arm_pass - base_pass) * 100.0 / len(pairs),
        "repairs": repairs,
        "regressions": regressions,
        "p_one_sided": mcnemar_one_sided(repairs, regressions),
    }


def conversation_endpoints(clusters: Mapping[str, Sequence[tuple]]) -> dict:
    any_pairs = []
    all_pairs = []
    for key in sorted(clusters):
        base = []
        arm = []
        for base_cells, arm_cells in clusters[key]:
            if len(base_cells) != len(arm_cells):
                raise ValueError("conversation cell width changed")
            base.extend(bool(x) for x in base_cells)
            arm.extend(bool(x) for x in arm_cells)
        if not base:
            raise ValueError("vacuous conversation cluster")
        any_pairs.append((any(base), any(arm)))
        all_pairs.append((all(base), all(arm)))
    return {"any": paired_endpoint(any_pairs), "all": paired_endpoint(all_pairs)}


def adjusted_aging_gap(cells: Sequence[Mapping]) -> dict:
    """Direct standardization over exact family x response-length strata."""
    if not cells:
        raise ValueError("cells required")
    strata = defaultdict(list)
    for cell in cells:
        strata[(str(cell["family"]), int(cell["length_bin"]))].append(cell)
    common = {
        key: rows
        for key, rows in strata.items()
        if {bool(row["aged"]) for row in rows} == {False, True}
    }
    common_n = sum(len(rows) for rows in common.values())
    if not common_n:
        raise ValueError("no fresh/aged common support")
    fresh_rate = 0.0
    aged_rate = 0.0
    detail = {}
    for key in sorted(common):
        rows = common[key]
        fresh = [bool(row["pass"]) for row in rows if not bool(row["aged"])]
        aged = [bool(row["pass"]) for row in rows if bool(row["aged"])]
        weight = len(rows) / common_n
        fr = sum(fresh) / len(fresh)
        ar = sum(aged) / len(aged)
        fresh_rate += weight * fr
        aged_rate += weight * ar
        detail[f"{key[0]}|len{key[1]}"] = {
            "n": len(rows),
            "weight": weight,
            "fresh_rate": fr,
            "aged_rate": ar,
        }
    return {
        "common_support_cells": common_n,
        "excluded_cells": len(cells) - common_n,
        "adjusted_fresh_rate": fresh_rate,
        "adjusted_aged_rate": aged_rate,
        "fresh_minus_aged_points": (fresh_rate - aged_rate) * 100.0,
        "strata": detail,
    }
