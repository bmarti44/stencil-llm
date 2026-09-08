import copy

import pytest

from stencil import source_replay_screen as screen


def check(identifier, symbol, value, expected, start, through, sources, behavior):
    return {
        "check_id": identifier,
        "symbol": symbol,
        "input": value,
        "expected_values": [expected],
        "active_from_round": start,
        "active_through_round": through,
        "source_ids": sources,
        "behavior": behavior,
        "rationale": "The cited source specifies this case.",
    }


def project(project_id="replay-01"):
    rounds = []
    private = []
    targets = ("alpha", "beta", "alpha")
    public_cases = (
        check("pub-1", "alpha", 1, 1, 1, 1, ["m01"], "functionality"),
        check("pub-2", "beta", 2, 2, 2, 3, ["m06"], "functionality"),
        check("pub-3", "alpha", 3, 3, 3, None, ["m11"], "functionality"),
    )
    private_cases = (
        [
            check("p1-new", "alpha", 10, 10, 1, 1, ["m01"], "functionality"),
            check("p1-ret-a", "alpha", -1, -1, 1, 3, ["m02"], "retained"),
            check("p1-ret-b", "beta", 7, 7, 1, 3, ["m03"], "retained"),
        ],
        [
            check("p2-new", "beta", 8, 8, 2, 3, ["m06"], "functionality"),
            check("p2-old-a", "alpha", -2, -2, 2, 3, ["m02", "m07"], "retirement"),
            check("p2-old-b", "beta", 9, 9, 2, 3, ["m08"], "retirement"),
        ],
        [
            check("p3-new", "alpha", 4, 4, 3, None, ["m11"], "functionality"),
            check("p3-old-a", "alpha", 5, 5, 3, None, ["m12"], "retirement"),
            check("p3-old-b", "beta", 6, 6, 3, None, ["m13"], "retirement"),
        ],
    )
    references = (
        "def alpha(x):\n    return x\n",
        "def beta(x):\n    return x\n",
        "def alpha(x):\n    return x\n",
    )
    for offset in range(3):
        first = offset * 5 + 1
        sources = [
            {
                "message_id": f"m{first + index:02d}",
                "role": "user",
                "text": f"source {first + index}",
            }
            for index in range(4)
        ]
        request = {
            "message_id": f"m{first + 4:02d}",
            "role": "user",
            "text": f"request {offset + 1}",
        }
        rounds.append(
            {
                "index": offset + 1,
                "source_messages": sources,
                "request": request,
                "target": {"path": "module.py", "symbol": targets[offset]},
                "public_checks": [public_cases[offset]],
            }
        )
        private.append(
            {
                "index": offset + 1,
                "reference_patch": references[offset],
                "checks": private_cases[offset],
            }
        )
    return {
        "schema_version": 1,
        "author": "kimi-k3:cloud",
        "lineage": "Fresh independent authorship with no reused benchmark.",
        "public": {
            "project_id": project_id,
            "description": "Tiny synthetic validation project.",
            "initial_file": {
                "path": "module.py",
                "text": "def alpha(x):\n    return x\n\ndef beta(x):\n    return x\n",
            },
            "rounds": rounds,
        },
        "private": {
            "rounds": private,
            "obsolete_mutant": {
                "source": "def alpha(x):\n    return x + 1\n",
                "failing_check_id": "p3-old-a",
            },
        },
    }


def test_strict_project_validation_and_public_projection():
    document = project()
    validated = screen.validate_project(document)
    assert validated == document and validated is not document
    projection = screen.public_project(validated)
    assert set(projection) == {"project_id", "description", "initial_file", "rounds"}
    assert set(projection["rounds"][0]["public_checks"][0]) == {
        "check_id",
        "symbol",
        "input",
        "expected_values",
    }
    assert "private" not in repr(projection)

    bad = copy.deepcopy(document)
    bad["extra"] = True
    with pytest.raises(ValueError):
        screen.validate_project(bad)
    bad = copy.deepcopy(document)
    bad["public"]["initial_file"]["text"] = "def alpha(x: int):\n    return x\n"
    with pytest.raises(ValueError, match="annotation"):
        screen.validate_project(bad)

    for malformed_behavior in ([], {}):
        bad = copy.deepcopy(document)
        bad["private"]["rounds"][0]["checks"][0]["behavior"] = malformed_behavior
        with pytest.raises(ValueError, match="behavior"):
            screen.validate_project(bad)


def test_original_eligibility_active_intervals_and_conflicts():
    document = screen.validate_project(project())
    assert [len(screen.eligible_originals(document, index)) for index in (1, 2, 3)] == [
        4,
        9,
        14,
    ]
    assert [item["message_id"] for item in screen.recency_originals(document, 3)] == [
        "m11",
        "m12",
        "m13",
        "m14",
    ]
    public, private = screen.active_checks(document, 2)
    assert {item["check_id"] for item in public} == {"pub-2"}
    assert "p1-ret-a" in {item["check_id"] for item in private}
    assert "p1-new" not in {item["check_id"] for item in private}

    bad = project()
    conflict = copy.deepcopy(bad["private"]["rounds"][1]["checks"][0])
    conflict.update(check_id="conflict", symbol="alpha", input=-1, expected_values=[99])
    bad["private"]["rounds"][1]["checks"].append(conflict)
    with pytest.raises(ValueError, match="conflicting active"):
        screen.validate_project(bad)


def test_schedule_has_all_48_slots_with_rotation_and_adjacent_selection():
    documents = [
        screen.validate_project(project(f"replay-{index:02d}")) for index in range(1, 5)
    ]
    slots = screen.planned_slots(documents)
    assert len(slots) == 48
    assert [slot["slot_index"] for slot in slots] == list(range(48))
    assert sum(slot["kind"] == "selector" for slot in slots) == 12
    assert sum(slot["kind"] == "worker" for slot in slots) == 36
    workers = [
        slot
        for slot in slots
        if slot["project_index"] == 0
        and slot["round_index"] == 1
        and slot["kind"] == "worker"
    ]
    assert [slot["arm"] for slot in workers] == ["H", "S", "R"]
    for index, slot in enumerate(slots):
        if slot["kind"] == "selector":
            assert slots[index + 1]["kind"] == "worker"
            assert slots[index + 1]["arm"] == "S"


def _round_records(s=(3, 3, 3, 3), h=(2, 2, 2, 1), r=(2, 2, 2, 2)):
    records = []
    for project_index in range(4):
        for round_index in range(1, 4):
            for arm, counts in (("H", h), ("S", s), ("R", r)):
                records.append(
                    {
                        "project_index": project_index,
                        "round_index": round_index,
                        "arm": arm,
                        "successful": round_index <= counts[project_index],
                    }
                )
    return records


def _call_records():
    records = []
    for index in range(48):
        selector = index % 4 == 0
        arm = "S" if selector else ("H" if index % 2 else "R")
        records.append(
            {
                "status": "COMPLETE",
                "arm": arm,
                "kind": "selector" if selector else "worker",
                "usage": {"prompt_tokens": 5, "completion_tokens": 1},
                "http_elapsed_seconds": 0.5,
            }
        )
    # Make all denominators unambiguous and S safely within twice H.
    records.extend(
        {
            "status": "COMPLETE",
            "arm": "H",
            "kind": "worker",
            "usage": {"prompt_tokens": 10, "completion_tokens": 1},
            "http_elapsed_seconds": 1.0,
        }
        for _ in range(20)
    )
    return records


def test_practical_gate_and_registered_negative_controls():
    evidence = {
        "events": [],
        "schedule_automatic": True,
        "manual_action_interface": False,
        "retries": 0,
        "actual_requests_recorded": True,
    }
    result = screen.evaluate_gate(
        _round_records(), _call_records(), evidence, expected_slots=68
    )
    assert result["disposition"] == "PASS"
    assert all(result["criteria"].values())

    costly = _call_records()
    for item in costly:
        if item["arm"] == "S":
            item["usage"] = {"prompt_tokens": 1000, "completion_tokens": 1000}
    assert not screen.evaluate_gate(
        _round_records(), costly, evidence, expected_slots=68
    )["criteria"]["token_cost"]
    no_help = dict(evidence, actual_requests_recorded=False)
    assert not screen.evaluate_gate(
        _round_records(), _call_records(), no_help, expected_slots=68
    )["criteria"]["no_intervention"]


def test_projection_uses_frozen_formula():
    value = screen.projected_seconds(
        case_executions=120, max_check_seconds=0.1, max_render_seconds=0.02
    )
    expected = 600 + 2041.199447651 + max(120, 120 * 0.1 + 48 * 0.02 + 60) + 60
    assert value == expected
