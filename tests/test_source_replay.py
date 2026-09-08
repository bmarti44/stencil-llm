import copy
import json

import pytest

from stencil import source_replay as replay


def _message(identifier, text):
    return {"message_id": identifier, "role": "user", "text": text}


def test_selected_sources_round_trip_original_text_role_id_and_order():
    originals = [
        _message("m01", 'Keep café spelling, quote "x", and this newline:\nnext.'),
        _message("m02", "second"),
        _message("m03", "third"),
    ]
    untouched = copy.deepcopy(originals)

    selected = replay.select_originals(originals, ["m03", "m01"])
    evidence = replay.render_evidence(originals, ["m03", "m01"])
    decoded = json.loads(evidence["content"].split("\n", 1)[1])

    assert selected == [originals[0], originals[2]]
    assert decoded == selected
    assert originals == untouched
    assert "\\nnext" in evidence["content"]
    assert "café" in evidence["content"]


def test_empty_selection_still_renders_an_explicit_ephemeral_message():
    evidence = replay.render_evidence([_message("m01", "source")], [])

    assert evidence == {
        "role": "user",
        "content": replay.EVIDENCE_INTRODUCTION + "\n[]",
    }


@pytest.mark.parametrize(
    "identifiers,error",
    [
        (["m01", "m01"], "unique"),
        (["missing"], "eligible"),
        (["m01", "m02", "m03", "m04", "m05"], "at most 4"),
    ],
)
def test_selection_rejects_duplicate_unknown_and_over_count_ids(identifiers, error):
    messages = [_message(f"m0{index}", str(index)) for index in range(1, 6)]

    with pytest.raises(ValueError, match=error):
        replay.select_originals(messages, identifiers)


def test_original_message_utf8_boundary_and_duplicate_ids():
    replay.validate_originals([_message("m01", "é" * 320)])

    with pytest.raises(ValueError, match="640 UTF-8 bytes"):
        replay.validate_originals([_message("m01", "é" * 320 + "x")])
    with pytest.raises(ValueError, match="unique"):
        replay.validate_originals([_message("m01", "first"), _message("m01", "second")])


def test_selector_input_is_canonical_and_contains_only_original_public_text():
    originals = [_message("m01", "source")]
    request = _message("m02", "change the function")

    messages = replay.build_selector_messages(originals, request)
    body = json.loads(messages[1]["content"])

    assert messages[0] == {"role": "system", "content": replay.SELECTOR_INSTRUCTION}
    assert body == {
        "current_request": request,
        "eligible_sources": [
            {"message_id": "m01", "order": 1, "role": "user", "text": "source"}
        ],
    }
    assert "reference" not in messages[1]["content"]
    assert "expected_values" not in messages[1]["content"]


def test_work_envelope_redacts_check_metadata_and_history_omits_supplement():
    check = {
        "check_id": "pub-1",
        "symbol": "change",
        "input": 2,
        "expected_values": [3],
        "active_from_round": 1,
        "active_through_round": None,
        "source_ids": ["m01"],
        "behavior": "retained",
        "rationale": "private author reasoning",
    }
    target = {"path": "module.py", "symbol": "change"}
    envelope = replay.build_work_envelope(
        "def change(x):\n    return x\n", target, [check]
    )
    supplement = replay.render_evidence([_message("m01", "source")], ["m01"])
    base = [{"role": "system", "content": "system"}]
    original_base = copy.deepcopy(base)
    assistant = {"role": "assistant", "content": ""}
    tool = {
        "role": "tool",
        "tool_call_id": "call-1",
        "name": "replace_function",
        "content": "{}",
    }

    issued = replay.build_issued_messages(base, envelope, supplement)
    permanent = replay.commit_permanent_history(base, envelope, assistant, tool)
    decoded = json.loads(envelope["content"].split("\n", 1)[1])

    assert base == original_base
    assert issued == [base[0], supplement, envelope]
    assert permanent == [base[0], envelope, assistant, tool]
    assert supplement not in permanent
    assert decoded["public_checks"] == [
        {"check_id": "pub-1", "symbol": "change", "input": 2, "expected_values": [3]}
    ]
    assert "rationale" not in envelope["content"]
