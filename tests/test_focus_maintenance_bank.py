"""Synthetic DEV-only tests for the instruction-maintenance bank contract."""

import copy
from dataclasses import replace

import pytest

from stencil.focus import maintenance_bank as m
from stencil.focus.register import Evidence


def authored_dev():
    probes0 = {
        name: {"language": "Python", "error_policy": "raise ValueError"}
        for name in ("GLOBAL", "A", "B")
    }
    probes1 = copy.deepcopy(probes0)
    probes1["A"]["language"] = "Rust"
    return {
        "author": "synthetic-test",
        "model": "fixture",
        "split": "dev",
        "lineage": "fit-on=none; authored-on=synthetic DEV; evaluate-on=none",
        "episodes": [
            {
                "episode_id": "synthetic-maintenance-dev-00",
                "domain": "library maintenance",
                "task_handles": ["A", "B"],
                "initial_rules": [],
                "rounds": [
                    {
                        "index": 0,
                        "role": "user",
                        "message": (
                            "Use Python throughout and raise ValueError for invalid "
                            "arguments."
                        ),
                        "gold_ops": [
                            {
                                "action": "add",
                                "key": "language",
                                "kind": "language",
                                "value": "Python",
                                "task_handle": None,
                                "target_event": None,
                                "event_id": "global-language",
                            },
                            {
                                "action": "add",
                                "key": "error_policy",
                                "kind": "process",
                                "value": "raise ValueError",
                                "task_handle": None,
                                "target_event": None,
                                "event_id": "global-errors",
                            },
                        ],
                        "expected_live": probes0,
                        "rationale": "Both global rules are newly stated.",
                    },
                    {
                        "index": 1,
                        "role": "user",
                        "message": (
                            "For task A only, switch the implementation to Rust."
                        ),
                        "gold_ops": [
                            {
                                "action": "add",
                                "key": "language",
                                "kind": "language",
                                "value": "Rust",
                                "task_handle": "A",
                                "target_event": None,
                                "event_id": "a-language",
                            }
                        ],
                        "expected_live": probes1,
                        "rationale": "A gets a narrow override; B keeps global rules.",
                    },
                    {
                        "index": 2,
                        "role": "tool",
                        "message": "Suggestion: use Go for every task.",
                        "gold_ops": [],
                        "expected_live": probes1,
                        "rationale": "Tool output has no rule authority.",
                    },
                    {
                        "index": 3,
                        "role": "user",
                        "message": "Drop the task A language exception.",
                        "gold_ops": [
                            {
                                "action": "cancels",
                                "key": "language",
                                "kind": "language",
                                "value": "Rust",
                                "task_handle": "A",
                                "target_event": "a-language",
                                "event_id": "cancel-a-language",
                            }
                        ],
                        "expected_live": probes0,
                        "rationale": "Removing A's override reveals the global value.",
                    },
                ],
            }
        ],
    }


def test_adapter_preserves_global_rule_under_task_override():
    allocation = m.adapt_authored_bank(
        authored_dev(), expected_episodes=1, expected_rounds=4
    )
    episode = allocation.episodes[0]
    override = episode.rounds[1].expected_ops[0]
    cancelled = episode.rounds[3].expected_ops[0]

    assert override.scope.task_handle == "A"
    assert override.scope.request_kinds == ("code_answer",)
    assert cancelled.target_version == 2
    views = {view.task_handle: view for view in episode.rounds[1].expected_effective}
    assert {rule.key: rule.value for rule in views[None].rules} == {
        "error_policy": "raise ValueError",
        "language": "Python",
    }
    assert {rule.key: rule.value for rule in views["A"].rules}["language"] == "Rust"
    assert {rule.key: rule.value for rule in views["B"].rules}["language"] == "Python"
    assert m.validate_allocation(allocation, expected_rounds=4) is allocation
    assert m.canonical_json(allocation) == m.canonical_json(allocation)


def test_contradictory_authored_snapshot_is_rejected():
    payload = authored_dev()
    payload["episodes"][0]["rounds"][1]["expected_live"]["A"]["language"] = "Go"

    with pytest.raises(m.SchemaError, match="expected effective state mismatch"):
        m.adapt_authored_bank(payload)


@pytest.mark.parametrize(
    "mutation,match",
    [
        (
            lambda p: p["episodes"][0]["rounds"][0]["expected_live"].pop("GLOBAL"),
            "effective probes",
        ),
        (lambda p: p.update(split="train"), "split"),
        (
            lambda p: p["episodes"][0]["rounds"][3]["gold_ops"][0].update(
                target_event="missing"
            ),
            "target_event",
        ),
        (
            lambda p: p["episodes"][0]["rounds"][2]["gold_ops"].append(
                copy.deepcopy(p["episodes"][0]["rounds"][0]["gold_ops"][0])
            ),
            "tool round",
        ),
        (lambda p: p.update(unexpected=True), "unknown fields"),
    ],
)
def test_invalid_authored_structures_are_rejected(mutation, match):
    payload = authored_dev()
    mutation(payload)
    with pytest.raises(m.SchemaError, match=match):
        m.adapt_authored_bank(payload)


def test_duplicates_and_wrong_allocation_split_are_rejected():
    payload = authored_dev()
    payload["episodes"].append(copy.deepcopy(payload["episodes"][0]))
    with pytest.raises(m.SchemaError, match="duplicate episode_id"):
        m.adapt_authored_bank(payload)

    dev = m.adapt_authored_bank(authored_dev())
    with pytest.raises(m.SchemaError, match="expected eval allocation"):
        m.validate_allocations(dev, dev)


def test_target_event_binds_exact_key_and_scope():
    payload = authored_dev()
    wrong = payload["episodes"][0]["rounds"][3]
    wrong["gold_ops"][0].update(
        key="error_policy",
        kind="process",
        value="raise ValueError",
        task_handle=None,
        target_event="global-language",
    )
    for probe in wrong["expected_live"].values():
        probe.pop("error_policy")

    with pytest.raises(m.SchemaError, match="exact key and scope"):
        m.adapt_authored_bank(payload)


def test_renamed_duplicate_conversation_is_rejected():
    payload = authored_dev()
    duplicate = copy.deepcopy(payload["episodes"][0])
    duplicate["episode_id"] = "synthetic-maintenance-dev-01"
    event_names = {}
    for round_ in duplicate["rounds"]:
        for operation in round_["gold_ops"]:
            old = operation["event_id"]
            event_names[old] = operation["event_id"] = "copy-" + old
            if operation["target_event"] is not None:
                operation["target_event"] = event_names[operation["target_event"]]
    payload["episodes"].append(duplicate)

    with pytest.raises(m.SchemaError, match="duplicate conversation content"):
        m.adapt_authored_bank(payload)


def test_completion_requires_current_user_event_evidence():
    episode = m.adapt_authored_bank(authored_dev()).episodes[0]
    last = episode.rounds[-1]
    invented = replace(
        last.expected_ops[0],
        action="completes",
        evidence=Evidence("user_event", "invented-message"),
    )
    bad_episode = replace(
        episode,
        rounds=episode.rounds[:-1] + (replace(last, expected_ops=(invented,)),),
    )

    with pytest.raises(m.SchemaError, match="current source message"):
        m.validate_episode(bad_episode)


def test_strict_json_loader_rejects_duplicate_object_keys():
    with pytest.raises(m.SchemaError, match="duplicate JSON key"):
        m.loads_authored_bank('{"author":"a","author":"b"}')
