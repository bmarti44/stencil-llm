# ruff: noqa: E501
"""E2 synthetic multi-turn session generator (EVF-PLAN E2; TDD green).

Mirrors Multi-IF's SHAPE — turn 1 poses a task with constraints, turns
2-3 add constraints while every earlier one still binds (cumulative
instruction lists) — with our own topics, phrasings, and values (v4.3
_draw machinery), leak-firewalled against Multi-IF by the registered
kwargs/phrase checks (tests/test_b3_gen_mt.py). Sessions carry no
canonicals: the causal-moment harvest rolls the model's own
generations and branches them.
"""
import random

from stencil.b3_gen43 import (
    DEV_TOPICS,
    TRAIN_TOPICS,
    V43,
    _draw,
    combo_ok,
)

FOLLOWUP_TASKS = [
    "Now extend the piece with a short additional paragraph continuing the account.",
    "Now add a brief closing section for the same newsletter piece.",
    "Now revise and continue the piece with one more short passage.",
]

STILL_BINDING = ("Every earlier constraint from this conversation still applies "
                 "to this reply as well.")


def _draw_turn_combo(rng, existing, keys):
    """draw 1-2 NEW constraint keys jointly compatible with `existing`."""
    for _ in range(300):
        n_new = rng.choice((1, 2))
        cand = rng.sample([k for k in keys if k not in existing], n_new)
        if combo_ok(sorted(existing + cand)):
            return sorted(cand)
    return None


def generate_sessions(seed, n_sessions, split):
    rng = random.Random(seed)
    topics = TRAIN_TOPICS if split == "train" else DEV_TOPICS
    keys = sorted(k for k in V43 if k not in ("json_fmt", "two_resp"))  # singletons cannot accumulate
    sessions = []
    attempts = 0
    while len(sessions) < n_sessions:
        attempts += 1
        if attempts > n_sessions * 80:
            raise RuntimeError("generator failed to fill quota")
        topic = rng.choice(topics)
        task1 = f"Write a short account of {topic} for a neighborhood newsletter."
        base_sents_stub = ["stub."] * 12  # _draw only uses counts for thresholds
        combo_all, kwargs_all, phrases_all = [], {}, {}
        turns = []
        ok = True
        for ti in range(3):
            new = _draw_turn_combo(rng, combo_all, keys)
            if new is None:
                ok = False
                break
            try:
                kw, values, phrases = _draw(rng, sorted(combo_all + new), topic, base_sents_stub)
            except IndexError:
                ok = False
                break
            # keep prior draws stable: only adopt the NEW keys' draws;
            # ACQUISITION order so cumulative lists extend stably (Multi-IF semantics)
            for k in new:
                kwargs_all[k] = kw[k]
                phrases_all[k] = phrases[k]
            combo_all = combo_all + new
            task = task1 if ti == 0 else rng.choice(FOLLOWUP_TASKS)
            phrase_txt = " ".join(phrases_all[k] for k in new)
            prompt = task + " " + phrase_txt + ("" if ti == 0 else " " + STILL_BINDING)
            turns.append({
                "prompt": prompt,
                "new_combo": new,
                "combo": list(combo_all),
                "instruction_id_list": [V43[k]["iid"] for k in combo_all],
                "kwargs": [kwargs_all[k] for k in combo_all],
            })
        if not ok:
            continue
        # constrained words must not collide with the topic (v4.3 rule)
        cw = set()
        for k in combo_all:
            kwv = kwargs_all[k]
            cw |= set(kwv.get("keywords", [])) | set(kwv.get("forbidden_words", []))
            if "keyword" in kwv:
                cw.add(kwv["keyword"])
        if any(w in topic.lower() for w in cw):
            continue
        sessions.append({"key": len(sessions), "split": split, "topic": topic,
                         "turns": turns})
    return sessions
