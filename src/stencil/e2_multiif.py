"""Pure Multi-IF replay construction and registered E2 endpoint analysis."""

from __future__ import annotations

import hashlib
import json
import random
from collections import defaultdict
from collections.abc import Mapping, Sequence

from stencil.e2_stats import cluster_bootstrap_delta, mcnemar_one_sided

OPENER = "<|im_start|>assistant\n<think>\n\n</think>\n\n"


def seed_of(key, turn):
    return int(hashlib.sha256(f"{key}:{turn}".encode()).hexdigest()[:8], 16)


def turn_doc(row, turn):
    prompt = json.loads(row[f"turn_{turn}_prompt"])["content"]
    ids = json.loads(row[f"turn_{turn}_instruction_id_list"])
    kwargs = [json.loads(value) for value in json.loads(row[f"turn_{turn}_kwargs"])]
    return prompt, ids, kwargs


def score_turn(row, turn, response):
    from ifeval import utils as ifeval_utils

    prompt, ids, kwargs = turn_doc(row, turn)
    random.seed(seed_of(row["key"], turn))
    doc = {
        "key": 0,
        "prompt": prompt,
        "instruction_id_list": ids,
        "kwargs": kwargs,
    }
    return ifeval_utils.process_results(doc, [response])


def policy_branch(result, scores):
    return {
        "response": result.text,
        "response_sha256": hashlib.sha256(result.text.encode()).hexdigest(),
        "scores": scores,
        "n_generated": result.n_generated,
        "truncated": result.truncated,
        "timed_out": result.timed_out,
        "interventions": list(result.interventions),
        "biased_tokens": result.biased_tokens,
    }


def base_branch(record, turn):
    text = record["responses"][str(turn)]
    generation = record["gen"][str(turn)]
    return {
        "response": text,
        "response_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "scores": record["scores"][str(turn)],
        "n_generated": generation["n"],
        "truncated": bool(generation["truncated"]),
        "timed_out": bool(generation["timeout"]),
        "interventions": [],
        "biased_tokens": 0,
    }


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


def _analyze_arm(records, arm_name, bootstrap_draws):
    aged_pairs = []
    all_pairs = []
    prompt_pairs = defaultdict(list)
    clusters = defaultdict(list)
    aged_cluster_rows = []
    all_cluster_rows = []
    base_lengths = []
    arm_lengths = []
    base_truncations = arm_truncations = 0
    base_timeouts = arm_timeouts = 0
    fired = biased_tokens = evaluated_turns = 0
    for record in records:
        ordered_turns = sorted(
            record["turns"].items(), key=lambda item: int(item[0])
        )
        for turn, turn_record in ordered_turns:
            base = turn_record["base"]
            arm = turn_record["arms"][arm_name]
            base_cells = [bool(x) for x in base["scores"]["inst_level_strict_acc"]]
            arm_cells = [bool(x) for x in arm["scores"]["inst_level_strict_acc"]]
            if len(base_cells) != len(arm_cells):
                raise ValueError("arm changed constraint count")
            aged_count = int(turn_record["aged_count"])
            if not 0 < aged_count <= len(base_cells):
                raise ValueError("invalid aged constraint count")
            base_aged = base_cells[:aged_count]
            arm_aged = arm_cells[:aged_count]
            aged_pairs.extend(zip(base_aged, arm_aged, strict=True))
            all_pairs.extend(zip(base_cells, arm_cells, strict=True))
            clusters[str(record["key"])].append((base_aged, arm_aged))
            aged_cluster_rows.append(
                {"conversation": int(record["ci"]), "base": base_aged, "arm": arm_aged}
            )
            all_cluster_rows.append(
                {
                    "conversation": int(record["ci"]),
                    "base": base_cells,
                    "arm": arm_cells,
                }
            )
            prompt_pair = (
                bool(base["scores"]["prompt_level_strict_acc"]),
                bool(arm["scores"]["prompt_level_strict_acc"]),
            )
            prompt_pairs[str(turn)].append(prompt_pair)
            prompt_pairs["pooled"].append(prompt_pair)
            base_lengths.append(int(base["n_generated"]))
            arm_lengths.append(int(arm["n_generated"]))
            base_truncations += int(base["truncated"])
            arm_truncations += int(arm["truncated"])
            base_timeouts += int(base["timed_out"])
            arm_timeouts += int(arm["timed_out"])
            fired += int(
                any(
                    event.get("kind") == "onset"
                    for event in arm.get("interventions", ())
                )
            )
            biased_tokens += int(arm.get("biased_tokens", 0))
            evaluated_turns += 1
    return {
        "aged_constraints": paired_endpoint(aged_pairs),
        "all_constraints": paired_endpoint(all_pairs),
        "conversation_aged": conversation_endpoints(clusters),
        "aged_cluster_bootstrap": cluster_bootstrap_delta(
            aged_cluster_rows, draws=bootstrap_draws, seed=0
        ),
        "all_cluster_bootstrap": cluster_bootstrap_delta(
            all_cluster_rows, draws=bootstrap_draws, seed=0
        ),
        "strict_prompt": {
            key: paired_endpoint(value) for key, value in sorted(prompt_pairs.items())
        },
        "controls": {
            "evaluated_turns": evaluated_turns,
            "base_mean_tokens": sum(base_lengths) / len(base_lengths),
            "arm_mean_tokens": sum(arm_lengths) / len(arm_lengths),
            "base_truncations": base_truncations,
            "arm_truncations": arm_truncations,
            "base_timeouts": base_timeouts,
            "arm_timeouts": arm_timeouts,
            "fired_rows": fired,
            "firing_rate": fired / evaluated_turns,
            "biased_tokens": biased_tokens,
        },
    }


def analyze_replay_records(
    records: Sequence[Mapping], *, diagnostic: bool, bootstrap_draws: int = 10_000
) -> dict:
    selected = [
        record for record in records if bool(record["diagnostic"]) is diagnostic
    ]
    if not selected:
        raise ValueError("requested Multi-IF partition is empty")
    arm_names = ("ctrb", "periodic", "fixed_oldest", "positive_control")
    arms = {
        arm: _analyze_arm(selected, arm, bootstrap_draws) for arm in arm_names
    }
    reasons = []
    if not diagnostic:
        primary = arms["ctrb"]["aged_constraints"]
        if primary["delta_points"] < 2.0:
            reasons.append(
                f"aged-constraint delta {primary['delta_points']:.4f} < +2.0 points"
            )
        if primary["p_one_sided"] >= 0.05:
            reasons.append(
                f"aged-constraint McNemar p {primary['p_one_sided']:.6g} >= 0.05"
            )
        ctrb_controls = arms["ctrb"]["controls"]
        if ctrb_controls["arm_truncations"] > ctrb_controls["base_truncations"]:
            reasons.append("CTRB has excess truncations")
        if ctrb_controls["arm_timeouts"] > ctrb_controls["base_timeouts"]:
            reasons.append("CTRB has excess timeouts")
        for comparator in ("periodic", "fixed_oldest"):
            delta = arms[comparator]["aged_constraints"]["delta_points"]
            if primary["delta_points"] <= delta:
                reasons.append(
                    f"CTRB aged delta does not beat {comparator} ({delta:.4f})"
                )
    return {
        "partition": "diagnostic" if diagnostic else "primary",
        "conversations": len(selected),
        "arms": arms,
        "gate_pass": None if diagnostic else not reasons,
        "failure_reasons": reasons,
    }
