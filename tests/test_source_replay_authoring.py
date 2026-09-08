import copy

import pytest

from stencil import source_replay_authoring as authoring


def scaffold_response():
    return {
        "description": "Synthetic staged project.",
        "lineage": "Fresh synthetic test fixture with fit-on none.",
        "initial_source": (
            "def alpha(x):\n    return x\n\ndef beta(x):\n    return x\n"
        ),
        "rounds": [
            {
                "source_texts": [
                    f"round {round_index} source {item}" for item in range(1, 5)
                ],
                "target_symbol": symbol,
            }
            for round_index, symbol in ((1, "alpha"), (2, "beta"), (3, "alpha"))
        ],
    }


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
        "rationale": "The cited source requires this synthetic behavior.",
    }


def packets():
    return [
        {
            "reference_patch": "def alpha(x):\n    return x\n",
            "public_checks": [
                check("pub-1", "alpha", 1, 1, 1, 1, ["m01"], "functionality")
            ],
            "private_checks": [
                check("p1-new", "alpha", 10, 10, 1, 1, ["m01"], "functionality"),
                check("p1-keep-a", "alpha", -1, -1, 1, 3, ["m02"], "retained"),
                check("p1-keep-b", "beta", 7, 7, 1, 3, ["m03"], "retained"),
            ],
        },
        {
            "reference_patch": "def beta(x):\n    return x\n",
            "public_checks": [
                check("pub-2", "beta", 2, 2, 2, 3, ["m06"], "functionality")
            ],
            "private_checks": [
                check("p2-new", "beta", 8, 8, 2, 3, ["m06"], "functionality"),
                check("p2-old-a", "alpha", -2, -2, 2, 3, ["m07"], "retirement"),
                check("p2-old-b", "beta", 9, 9, 2, 3, ["m08"], "retirement"),
            ],
        },
        {
            "reference_patch": "def alpha(x):\n    return x\n",
            "public_checks": [
                check("pub-3", "alpha", 3, 3, 3, None, ["m11"], "functionality")
            ],
            "private_checks": [
                check("p3-new", "alpha", 4, 4, 3, None, ["m11"], "functionality"),
                check("p3-old-a", "alpha", 5, 5, 3, None, ["m12"], "retirement"),
                check("p3-old-b", "beta", 6, 6, 3, None, ["m13"], "retirement"),
            ],
            "obsolete_mutant": {
                "source": "def alpha(x):\n    return x + 1\n",
                "failing_check_id": "p3-old-a",
            },
        },
    ]


@pytest.mark.parametrize(
    "body",
    [
        b'{"description":"a","description":"b"}',
        b'{"value":NaN}',
        b"```json\n{}\n```",
        b'{"partial":',
        b"{} trailing",
    ],
)
def test_strict_author_json_rejects_noncanonical_envelopes(body):
    with pytest.raises(ValueError):
        authoring.parse_author_json(body)


def test_prompt_rendering_is_one_pass_and_preserves_inserted_dollars():
    scaffold_template = "ID=$project_id DOMAIN=$domain"
    rendered = authoring.render_scaffold_prompt(
        scaffold_template, "$project", "cash $HOME and ${later}"
    )
    assert rendered == 'ID="$project" DOMAIN="cash $HOME and ${later}"'

    round_template = (
        "ID=$project_id ROUND=$round_index S=$scaffold P=$prior_packets "
        "C=$data_contract"
    )
    rendered = authoring.render_round_prompt(
        round_template,
        "$project",
        2,
        {"literal": "$HOME"},
        [{"value": "${later}"}],
        "contract $ marker",
    )
    assert '"literal":"$HOME"' in rendered
    assert '"value":"${later}"' in rendered
    assert rendered.endswith("C=contract $ marker")


def test_scaffold_assembly_is_exact_and_does_not_mutate_authored_fields():
    authored = scaffold_response()
    original = copy.deepcopy(authored)
    scaffold, lineage = authoring.assemble_scaffold("staged-01", authored)
    assert authored == original
    assert lineage == authored["lineage"]
    assert set(scaffold) == {"project_id", "description", "initial_file", "rounds"}
    assert [
        message["message_id"]
        for round_ in scaffold["rounds"]
        for message in [*round_["source_messages"], round_["request"]]
    ] == [f"m{index:02d}" for index in range(1, 16)]
    assert scaffold["rounds"][0]["request"]["text"] == authoring.request_text("alpha")
    assert "public_checks" not in scaffold["rounds"][0]


def test_packet_validation_rejects_future_source_and_overlapping_conflict():
    scaffold, _ = authoring.assemble_scaffold("staged-01", scaffold_response())
    bad = copy.deepcopy(packets()[0])
    bad["private_checks"][0]["source_ids"] = ["m06"]
    with pytest.raises(ValueError, match="visible"):
        authoring.validate_packet(scaffold, [], bad, 1)

    first = packets()[0]
    bad_second = copy.deepcopy(packets()[1])
    bad_second["private_checks"].append(
        check("conflict", "alpha", -1, 99, 2, 3, ["m06"], "functionality")
    )
    with pytest.raises(ValueError, match="conflicting"):
        authoring.validate_packet(scaffold, [first], bad_second, 2)


def test_references_are_applied_sequentially_through_real_consumers():
    scaffold, lineage = authoring.assemble_scaffold("staged-01", scaffold_response())
    accepted = []
    module = scaffold["initial_file"]["text"]
    records = []
    for round_index, packet in enumerate(packets(), 1):
        frozen, module, record = authoring.validate_and_apply_packet(
            scaffold, accepted, packet, round_index, module
        )
        accepted.append(frozen)
        records.append(record)
    project = authoring.assemble_project(scaffold, lineage, accepted)
    assert project["private"]["obsolete_mutant"] == packets()[2]["obsolete_mutant"]
    assert all(record["all_active_checks_passed"] for record in records)
    assert records[-1]["mutant"]["reference_designated_result"]["passed"] is True
    assert records[-1]["mutant"]["designated_result"]["passed"] is False


def test_deadline_after_actual_check_preserves_partial_execution_evidence():
    scaffold, _ = authoring.assemble_scaffold("staged-01", scaffold_response())
    deadline_checks = 0

    def deadline():
        nonlocal deadline_checks
        deadline_checks += 1
        if deadline_checks == 3:
            raise RuntimeError("synthetic whole deadline")

    with pytest.raises(authoring.StageExecutionInterrupted) as caught:
        authoring.validate_and_apply_packet(
            scaffold,
            [],
            packets()[0],
            1,
            scaffold["initial_file"]["text"],
            deadline_check=deadline,
        )
    record = caught.value.record
    assert len(record["public_results"]) == 1
    assert record["public_results"][0]["check_id"] == "pub-1"
    assert record["public_results"][0]["input"] == 1
    assert record["private_results"] == []


def test_deadline_after_mutant_check_preserves_mutant_execution_evidence():
    scaffold, _ = authoring.assemble_scaffold("staged-01", scaffold_response())
    accepted = []
    module = scaffold["initial_file"]["text"]
    for round_index, packet in enumerate(packets()[:2], 1):
        frozen, module, _ = authoring.validate_and_apply_packet(
            scaffold, accepted, packet, round_index, module
        )
        accepted.append(frozen)
    deadline_checks = 0

    def deadline():
        nonlocal deadline_checks
        deadline_checks += 1
        if deadline_checks == 23:
            raise RuntimeError("synthetic whole deadline after mutant")

    with pytest.raises(authoring.StageExecutionInterrupted) as caught:
        authoring.validate_and_apply_packet(
            scaffold,
            accepted,
            packets()[2],
            3,
            module,
            deadline_check=deadline,
        )
    mutant = caught.value.record["mutant"]
    assert mutant["designated_result"] is None
    assert len(mutant["results"]) == 1
    assert mutant["results"][0]["check_id"] == "p3-old-a"
    assert mutant["results"][0]["input"] == 5


def test_wrong_retired_rule_mutant_behavior_is_rejected():
    scaffold, _ = authoring.assemble_scaffold("staged-01", scaffold_response())
    accepted = packets()[:2]
    final = copy.deepcopy(packets()[2])
    final["obsolete_mutant"]["source"] = "def alpha(x):\n    return x\n"
    module = scaffold["initial_file"]["text"]
    for index, packet in enumerate(accepted, 1):
        _, module, _ = authoring.validate_and_apply_packet(
            scaffold, accepted[: index - 1], packet, index, module
        )
    with pytest.raises(ValueError, match="mutant"):
        authoring.validate_and_apply_packet(scaffold, accepted, final, 3, module)
