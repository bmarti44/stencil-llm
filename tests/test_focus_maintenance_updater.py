"""CPU tests for the isolated natural-message maintenance updater."""

import json

import pytest

from stencil.focus import maintenance_updater as updater
from stencil.focus.loop import Message
from stencil.focus.register import Entry, Register, Scope, Source


def _message(text="Use Python for all code.", *, role="user", message_id="m1"):
    return Message(message_id=message_id, role=role, text=text)


def _entry(
    action="add",
    *,
    key="language",
    value="Python",
    task_handle=None,
    target_version=None,
    event_id="seed-1",
):
    return Entry(
        action=action,
        key=key,
        scope=Scope(task_handle, ("code_answer",)),
        kind="language",
        value=value,
        text=f"Use {value}.",
        target_version=target_version,
        event_id=event_id,
        source=Source("user", "seed", (0, 11)),
    )


def _decoder(operations, *, base_override=None, calls=None):
    def decode(prompt):
        if calls is not None:
            calls.append(prompt)
        supplied = json.loads(prompt)["input"]["base_state_sha256"]
        return json.dumps(
            {
                "base_state_sha256": base_override or supplied,
                "operations": operations,
            }
        )

    return decode


def _add(*, key="language", value="Python", task_handle=None, text=None):
    return {
        "action": "add",
        "key": key,
        "scope": {
            "task_handle": task_handle,
            "request_kinds": ["code_answer"],
        },
        "kind": "language",
        "value": value,
        "text": text or f"Use {value}.",
        "evidence_span": [0, len("Use Python for all code.")],
    }


def _target(action, key, version, end):
    return {
        "action": action,
        "key": key,
        "target_version": version,
        "evidence_span": [0, end],
    }


def test_prompt_has_full_unicode_source_state_and_no_gold_interface():
    state = Register(task_handles={"A", "B"}).apply((_entry(),))
    source = _message("Use π in the explanation.", message_id="current")
    history = (_message("Earlier natural text.", message_id="past"),)
    calls = []

    result = updater.execute(
        state,
        source,
        _decoder([], calls=calls),
        past_messages=history,
        task_handles=("B", "A"),
    )

    assert result.accepted and result.register is state
    assert len(calls) == 1 and calls[0] == result.prompt
    shown = json.loads(result.prompt)
    assert shown["input"]["source"]["text"] == source.text
    assert shown["input"]["source"]["character_count"] == len(source.text)
    assert shown["input"]["history"][0]["text"] == history[0].text
    assert shown["input"]["state"]["versions"][0]["entry"]["value"] == "Python"
    assert shown["input"]["task_handles"] == ["A", "B"]
    assert "gold" not in result.prompt.lower()
    assert "rationale" not in result.prompt.lower()


def test_empty_state_prompt_documents_an_accepted_exact_wire_operation():
    state = Register(task_handles={"A"})
    source = _message("Keep this standing constraint active.")
    shown = json.loads(updater.build_prompt(state, source).text)
    schema = shown["response_schema"]
    variants = {
        item["properties"]["action"]["const"]: item
        for item in schema["properties"]["operations"]["items"]["oneOf"]
    }

    assert schema["required"] == ["base_state_sha256", "operations"]
    assert schema["additionalProperties"] is False
    assert set(variants) == {"add", "supersedes", "cancels", "reinstates"}
    expected_fields = {
        "add": {"action", "key", "scope", "kind", "value", "text", "evidence_span"},
        "supersedes": {
            "action",
            "key",
            "scope",
            "kind",
            "value",
            "text",
            "target_version",
            "evidence_span",
        },
        "cancels": {"action", "key", "target_version", "evidence_span"},
        "reinstates": {"action", "key", "target_version", "evidence_span"},
    }
    for action, fields in expected_fields.items():
        assert set(variants[action]["required"]) == fields
        assert set(variants[action]["properties"]) == fields
        assert variants[action]["additionalProperties"] is False
    add_schema = variants["add"]
    assert "target_version" not in add_schema["properties"]
    scope = add_schema["properties"]["scope"]
    assert scope["properties"]["task_handle"]["enum"] == [None, "A"]
    assert scope["properties"]["request_kinds"]["items"]["enum"] == ["code_answer"]
    assert set(add_schema["properties"]["kind"]["enum"]) == {
        "language",
        "style",
        "format",
        "process",
    }
    span = add_schema["properties"]["evidence_span"]
    assert span["maxItems"] == span["minItems"] == 2
    assert span["prefixItems"][0]["minimum"] == 0
    assert span["prefixItems"][1]["maximum"] == len(source.text)
    lifecycle = " ".join(shown["lifecycle_rules"])
    assert all(
        term in lifecycle
        for term in ("task override", "global", "Supersedes", "Cancels", "Reinstates")
    )

    operation = {
        "action": "add",
        "key": {"new": "standing-constraint"},
        "scope": {"task_handle": None, "request_kinds": ["code_answer"]},
        "kind": "process",
        "value": "active",
        "text": "Keep this constraint active.",
        "evidence_span": [0, len(source.text)],
    }
    result = updater.execute(state, source, _decoder([operation]))
    assert result.accepted and result.accepted_ops[0].value == "active"


def test_task_shadow_add_keeps_global_rule_live():
    state = Register(task_handles={"A", "B"}).apply((_entry(),))
    source = _message("For task A only, use Rust.")
    operation = _add(key="language", value="Rust", task_handle="A", text="Use Rust.")
    operation["evidence_span"] = [0, len(source.text)]

    result = updater.execute(state, source, _decoder([operation]))

    assert result.accepted
    assert {v.entry.value for v in result.register.live("A", "code_answer")} == {"Rust"}
    assert {v.entry.value for v in result.register.live("B", "code_answer")} == {
        "Python"
    }


def test_cancel_then_reinstate_inherits_target_fields():
    state = Register(task_handles={"A"}).apply((_entry(task_handle="A"),))
    cancel_source = _message("Drop that rule.", message_id="cancel")
    cancelled = updater.execute(
        state,
        cancel_source,
        _decoder([_target("cancels", "language", 1, len(cancel_source.text))]),
    )
    reinstate_source = _message("Bring that rule back.", message_id="reinstate")
    reinstated = updater.execute(
        cancelled.register,
        reinstate_source,
        _decoder([_target("reinstates", "language", 1, len(reinstate_source.text))]),
    )

    assert cancelled.accepted and cancelled.register.live("A", "code_answer") == ()
    assert reinstated.accepted
    latest = reinstated.register.live("A", "code_answer")[0]
    assert latest.version == 2
    assert latest.entry.scope == state.versions[0].entry.scope
    assert latest.entry.kind == "language"
    assert latest.entry.value == "Python"
    assert latest.entry.text == "Use Python."


def test_new_key_reference_is_host_allocated_and_usable_in_same_transaction():
    state = Register(task_handles={"A"})
    source = _message("Use Python, then revise that rule to Rust.")
    new_ref = {"new": "implementation-language"}
    add = _add(key=new_ref, text="Use Python.")
    add["evidence_span"] = [0, 10]
    supersede = {
        "action": "supersedes",
        "key": new_ref,
        "scope": {"task_handle": None, "request_kinds": ["code_answer"]},
        "kind": "language",
        "value": "Rust",
        "text": "Use Rust.",
        "target_version": 1,
        "evidence_span": [12, len(source.text)],
    }

    first = updater.execute(state, source, _decoder([add, supersede]))
    second = updater.execute(state, source, _decoder([add, supersede]))

    assert first.accepted and len(first.accepted_ops) == 2
    assert first.accepted_ops[0].key == first.accepted_ops[1].key
    assert first.accepted_ops[0].key.startswith("auto-key-")
    assert first.accepted_ops == second.accepted_ops
    assert first.register.live(None, "code_answer")[0].entry.value == "Rust"


def test_stale_hash_and_mixed_invalid_transaction_leave_original_state():
    state = Register(task_handles={"A"}).apply((_entry(task_handle="A"),))
    source = _message("Use Rust, and remove a missing version.")
    valid = {
        **_add(value="Rust", task_handle="A", text="Use Rust."),
        "action": "supersedes",
        "target_version": 1,
    }
    valid["evidence_span"] = [0, len(source.text)]
    invalid = _target("cancels", "language", 99, len(source.text))

    stale = updater.execute(state, source, _decoder([], base_override="0" * 64))
    mixed = updater.execute(state, source, _decoder([valid, invalid]))

    assert not stale.accepted and "stale base-state" in stale.error
    assert not mixed.accepted and "target_version" in mixed.error
    for rejected in (stale, mixed):
        assert rejected.register is state
        assert rejected.accepted_ops == ()
        assert rejected.pre_state_sha256 == rejected.post_state_sha256
    assert state.live("A", "code_answer")[0].entry.value == "Python"


def test_wrong_source_fields_target_scope_and_completion_are_rejected():
    state = Register(task_handles={"A"}).apply((_entry(task_handle="A"),))
    source = _message("Change this rule.")
    wrong_source = _target("cancels", "language", 1, len(source.text))
    wrong_source["source"] = {"role": "system", "message_id": "invented"}
    wrong_scope = {
        **_add(value="Rust", task_handle=None, text="Use Rust."),
        "action": "supersedes",
        "target_version": 1,
    }
    wrong_scope["evidence_span"] = [0, len(source.text)]
    completion = {
        "action": "completes",
        "key": "language",
        "target_version": 1,
        "evidence_span": [0, len(source.text)],
    }

    results = [
        updater.execute(state, source, _decoder([wrong_source])),
        updater.execute(state, source, _decoder([wrong_scope])),
        updater.execute(state, source, _decoder([completion])),
    ]

    assert all(not result.accepted and result.register is state for result in results)
    assert "unknown fields" in results[0].error
    assert "target scope" in results[1].error
    assert "unsupported action" in results[2].error


def test_non_user_source_is_called_once_but_cannot_mutate():
    state = Register(task_handles={"A"})
    calls = []

    result = updater.execute(
        state,
        _message("Suggestion: add a rule.", role="assistant"),
        _decoder([_add()], calls=calls),
    )

    assert not result.accepted and result.register is state
    assert "non-user source" in result.error
    assert len(calls) == 1

    noop = updater.execute(state, _message("Tool result.", role="tool"), _decoder([]))
    assert noop.accepted and noop.register is state


def test_unknown_origin_and_invented_existing_key_are_rejected():
    state = Register(task_handles={"A"})
    calls = []
    quoted = Message("m1", "user", "Use Python.", origin="quoted")
    bad_origin = updater.execute(state, quoted, _decoder([], calls=calls))
    operation = _add(key="model-chosen-key")
    bad_key = updater.execute(state, _message(), _decoder([operation]))

    assert quoted.adopted is False  # updater never rewrites the production envelope
    assert not bad_origin.accepted and calls == []
    assert "authenticated direct" in bad_origin.error
    assert not bad_key.accepted and "existing key" in bad_key.error


def test_noop_decoder_error_and_malformed_response_have_complete_receipts():
    state = Register(task_handles={"A"})
    source = _message()
    noop = updater.execute(state, source, _decoder([]))

    def explode(_prompt):
        raise RuntimeError("decoder unavailable")

    failed = updater.execute(state, source, explode)
    malformed = updater.execute(state, source, lambda _prompt: "{broken")

    assert noop.accepted and noop.accepted_ops == () and noop.register is state
    assert failed.raw_response is None and "decoder: RuntimeError" in failed.error
    assert malformed.raw_response == "{broken" and "JSON" in malformed.error
    for result in (noop, failed, malformed):
        assert result.prompt
        assert result.pre_state_sha256 == result.post_state_sha256


def test_out_of_range_unicode_span_rejects_without_lexical_inference():
    state = Register(task_handles={"A"})
    source = _message("π")
    operation = _add(key={"new": "symbol"}, text="anything")
    operation["evidence_span"] = [0, 2]
    rejected = updater.execute(state, source, _decoder([operation]))
    operation["evidence_span"] = [0, 1]
    accepted = updater.execute(state, source, _decoder([operation]))

    assert not rejected.accepted and "evidence_span" in rejected.error
    assert accepted.accepted
    assert accepted.accepted_ops[0].text == "anything"
    assert accepted.accepted_ops[0].source.span == (0, 1)


@pytest.mark.parametrize("bad_field", ["value", "text"])
def test_lone_surrogate_in_mixed_transaction_returns_atomic_raw_receipt(bad_field):
    state = Register(task_handles={"A"})
    source = _message()
    valid = _add(key={"new": "first"})
    invalid = _add(key={"new": "second"}, value="valid", text="valid")
    invalid[bad_field] = "\ud800"
    base = updater.build_prompt(state, source).base_state_sha256
    raw = json.dumps({"base_state_sha256": base, "operations": [valid, invalid]})

    result = updater.execute(state, source, lambda _prompt: raw)

    assert not result.accepted and "valid UTF-8" in result.error
    assert result.raw_response == raw
    assert result.register is state and result.accepted_ops == ()
    assert result.pre_state_sha256 == result.post_state_sha256


def test_oversize_source_is_rejected_whole_before_decode():
    calls = []
    source = _message("x" * (updater.MAX_SOURCE_CHARS + 1))
    result = updater.execute(
        Register(task_handles={"A"}), source, _decoder([], calls=calls)
    )

    assert not result.accepted and "source exceeds" in result.error
    assert calls == []
