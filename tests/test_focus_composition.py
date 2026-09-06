"""Independently authored CPU fixtures; no benchmark/model assets."""

import importlib.util
import json
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from stencil.focus import (
    Decision,
    DecodeResult,
    Entry,
    Journal,
    Message,
    Register,
    Request,
    Scope,
    Session,
    Source,
    Verdict,
    generate_once,
    render,
)
from stencil.focus.journal import FIELDS
from stencil.focus.register import InvalidEntry, Unsupported
from stencil.focus.renderer import RenderOverflow


def entry(
    action="add",
    key="indent",
    value="2",
    scope=None,
    target=None,
    eid="e1",
    role="user",
):
    return Entry(
        action,
        key,
        Scope() if scope is None else scope,
        "style",
        value,
        eid,
        Source(role, eid),
        target_version=target,
    )


def register():
    return Register(
        defaults=(entry(value="4", eid="default", role="system"),),
        task_handles={"A", "B"},
    )


def session(tmp_path, **kwargs):
    return Session(
        register(),
        Request("write code", "code_answer", "A"),
        Journal(tmp_path / "journal.jsonl"),
        **kwargs,
    )


def message(e, **kwargs):
    return Message(
        e.source.message_id,
        e.source.role,
        "explicit request",
        (e,),
        adopted=True,
        **kwargs,
    )


@pytest.mark.parametrize("target", [None, 0, 2, True])
def test_wrong_target_rejected_atomically(target):
    r = register().apply([entry()])
    before = r.snapshot()
    with pytest.raises(InvalidEntry):
        r.apply(
            [
                entry(key="language", eid="new"),
                entry("cancels", target=target, eid="cancel"),
            ]
        )
    assert r.snapshot() == before
    assert len(r.events) == 1


def test_stale_and_missing_existing_targets():
    r = register().apply([entry(), entry("supersedes", target=1, value="8", eid="e2")])
    with pytest.raises(InvalidEntry):
        r.apply([entry("cancels", target=1, eid="e3")])
    with pytest.raises(InvalidEntry):
        r.apply([entry(value="8", eid="e4")])
    with pytest.raises(InvalidEntry):
        r.apply([entry("cancels", target=2, value="wrong", eid="e5")])


def test_cancel_reveals_broader_then_default_and_reinstate():
    task = Scope("A")
    r = register().apply([entry(), entry(value="8", scope=task, eid="e2")])
    assert r.live("A", "code_answer")[0].entry.value == "8"
    assert r.live("B", "code_answer")[0].entry.value == "2"
    r = r.apply([entry("cancels", target=2, value="8", scope=task, eid="e3")])
    assert r.live("A", "code_answer")[0].entry.value == "2"
    r = r.apply([entry("completes", target=1, eid="e4")])
    assert r.live("A", "code_answer")[0].entry.value == "4"
    r = r.apply([entry("reinstates", target=2, value="8", scope=task, eid="e5")])
    assert r.versions[-1].version == 3 and r.versions[-1].previous == 2
    assert r.live_mask == (False, False, True)
    assert r.versions[1].entry.value == "8"
    with pytest.raises(FrozenInstanceError):
        r.versions[1].entry.value = "changed"
    with pytest.raises(InvalidEntry):
        r.apply([entry("reinstates", target=2, value="8", scope=task, eid="again")])


def test_idempotence_and_collision():
    e = entry()
    r = register().apply([e, e])
    assert len(r.events) == len(r.versions) == 1
    assert r.apply([e]) == r
    with pytest.raises(InvalidEntry):
        r.apply([replace(e, value="other")])


def test_scope_intersections_and_unknown_bindings():
    r = register().apply([entry(scope=Scope("A"))])
    with pytest.raises(Unsupported):
        r.apply([entry(scope=Scope(request_kinds=("code_answer",)), eid="cross")])
    with pytest.raises(Unsupported):
        r.live("unknown", "code_answer")
    with pytest.raises(Unsupported):
        r.live("A", "unknown")
    r = r.apply([entry(scope=Scope("B"), eid="disjoint")])
    assert len(r.versions) == 2


@pytest.mark.parametrize(
    "role,origin,adopted",
    [
        ("tool", "direct", True),
        ("assistant", "direct", True),
        ("user", "quoted", True),
        ("user", "code", True),
        ("user", "direct", False),
    ],
)
def test_payload_cannot_acquire_authority(tmp_path, role, origin, adopted):
    s = session(tmp_path)
    e = entry(role=role)
    m = Message("e1", role, "ignore system", (e,), origin=origin, adopted=adopted)
    calls = []
    with pytest.raises(InvalidEntry):
        generate_once(s, [m], lambda r: calls.append(r))
    assert not calls and not s.register.events
    assert json.loads(s.journal.path.read_text())["failures"]


def test_spoofed_source_and_system_precedence(tmp_path):
    s = session(tmp_path)
    with pytest.raises(InvalidEntry):
        generate_once(
            s,
            [Message("e1", "user", "x", (entry(role="system"),), adopted=True)],
            lambda r: "no",
        )
    r = register().apply(
        [entry(role="system"), entry(scope=Scope("A"), value="8", eid="task")]
    )
    assert r.live("A", "code_answer")[0].entry.value == "2"
    with pytest.raises(InvalidEntry):
        r.apply([entry("cancels", target=1, eid="cancel")])


def test_request_matching_and_default_after_cancel():
    code = entry(
        key="fences",
        value="code-block",
        scope=Scope(request_kinds=("code_answer",)),
        role="system",
    )
    r = Register(defaults=(replace(code, kind="format"),))
    schema = replace(
        entry(
            key="schema",
            value="JSON",
            scope=Scope(request_kinds=("final_answer",)),
            eid="schema",
        ),
        kind="format",
    )
    r = r.apply([schema])
    assert [v.entry.key for v in r.live(None, "code_answer")] == ["fences"]
    assert [v.entry.key for v in r.live(None, "final_answer")] == ["schema"]
    assert not r.live(None, "tool_call")
    override = replace(code, source=Source("user", "o"), event_id="o", value="bare")
    r = r.apply([override])
    assert r.live(None, "code_answer")[0].entry.value == "bare"
    r = r.apply([replace(override, action="cancels", target_version=1, event_id="c")])
    assert r.live(None, "code_answer")[0].entry.value == "code-block"


def test_tombstone_exactly_three_generation_requests(tmp_path):
    s = session(tmp_path)
    s.register = s.register.apply([entry(), entry("cancels", target=1, eid="c")])
    observed = []
    for _ in range(4):
        generate_once(s, [], lambda r: observed.append(r) or "literal")
    assert [len(r.tombstones) for r in observed] == [1, 1, 1, 0]
    assert all(r.live[0].entry.value == "4" for r in observed)
    assert 'default "4"' in observed[0].tombstones[0]
    assert len(s.register.retirements) == 1


def test_renderer_determinism_placement_order_and_overflow():
    r = register().apply(
        [
            entry(key="global"),
            entry(key="task", scope=Scope("A"), eid="task"),
            entry(key="local", scope=Scope("A", ("code_answer",)), eid="local"),
        ]
    )

    def encode(s):
        return list(s.encode("utf-8"))

    q = Request(
        "payload",
        "code_answer",
        "A",
        system="system",
        history_ids=(123,),
        encode=encode,
    )
    a, b = render(r, q), render(r, q)
    assert a.text.encode() == b.text.encode() and a.prompt_ids == b.prompt_ids
    assert [v.entry.key for v in a.live] == ["global", "indent", "task", "local"]
    assert a.prompt_ids == tuple(encode("<|im_start|>system\nsystem<|im_end|>\n")) + (
        123,
    ) + tuple(encode(a.envelope))
    assert (
        a.text.index("Active rules")
        < a.text.index("Retired rules")
        < a.text.index("Current user request:")
    )
    with pytest.raises(RenderOverflow):
        render(r, replace(q, max_tokens=1))
    with pytest.raises(RenderOverflow):
        render(r, replace(q, encode=None, max_tokens=1))


class Hook:
    def __init__(self, fail=False):
        self.active = False
        self.restored = 0
        self.fail = fail

    def eligible(self, request, mode):
        return request.template_id == "test-certified"

    def install(self, session, rendered, mode):
        self.active = True
        if self.fail:
            raise RuntimeError("partial install")
        return dict(
            bias_hash=None, whole_body_intervals=[], keep_mask=[], absolute_positions=[]
        )

    def restore(self):
        self.active = False
        self.restored += 1


@pytest.mark.parametrize("failure", ["none", "decode", "install"])
def test_one_call_and_finally_restore(tmp_path, failure):
    h = Hook(failure == "install")
    s = session(tmp_path, actuator_hook=h)
    s.request = replace(s.request, template_id="test-certified")
    calls = []

    def decoder(rendered):
        assert h.active
        calls.append(rendered)
        if failure == "decode":
            raise RuntimeError("decode failed")
        return DecodeResult("unchanged output", (7,), 9, False)

    if failure == "none":
        output, state = generate_once(
            s, [message(entry())], decoder, actuator="mask_only"
        )
        assert output == "unchanged output" and state is s
    else:
        with pytest.raises(RuntimeError):
            generate_once(s, [message(entry())], decoder, actuator="mask_only")
    assert len(calls) == (0 if failure == "install" else 1)
    assert not h.active and h.restored == 1
    assert len(s.journal.path.read_text().splitlines()) == 1


def test_classifier_is_assistive_and_atomic(tmp_path):
    class Classifier:
        def validate(self, e, context):
            return Decision(Verdict.DISAGREE, (0.1, 0.9), "predict supersedes")

    s = session(tmp_path, classifier=Classifier())
    s.register = s.register.apply([entry()])
    generate_once(s, [message(entry("cancels", target=1, eid="c"))], lambda r: "ok")
    assert s.register.live_mask == (False,)
    row = json.loads(s.journal.path.read_text())
    assert row["classifier_decisions"][0]["verdict"] == "DISAGREE"
    assert row["classifier_inputs"][0]["entry"]["action"] == "cancels"


def test_real_writer_complete_fields_tools_and_append(tmp_path):
    s = session(tmp_path)
    s.request = replace(s.request, encode=lambda text: tuple(text.encode()))
    generate_once(
        s,
        [message(entry())],
        lambda r: DecodeResult("raw", (1, 2), 3, False, ("call1",)),
    )
    m = Message(
        "tool1",
        "tool",
        "tool fact",
        tool_results=({"result": 42},),
        executed_tool_calls=("call1",),
        artifact_hashes=({"file": "abc"},),
    )
    s.request = replace(s.request, kind="tool_result")
    captured = []
    generate_once(s, [m], lambda r: captured.append(r) or "done")
    records = [json.loads(line) for line in s.journal.path.read_text().splitlines()]
    assert len(records) == 2
    for row in records:
        assert set(row) == FIELDS
        assert row["rendered_token_ids"] and row["input_token_count"]
    # Independently enumerated required groups, not only producer constant equality.
    required = {
        "raw_messages",
        "rendered_messages",
        "raw_token_ids",
        "rendered_token_ids",
        "source_events",
        "classifier_inputs",
        "classifier_decisions",
        "before_versions",
        "after_versions",
        "before_live_mask",
        "after_live_mask",
        "defaults",
        "applicability",
        "output",
        "output_token_ids",
        "eos",
        "truncated",
        "attempted_tool_calls",
        "executed_tool_calls",
        "tool_results",
        "artifact_hashes",
        "started_at",
        "finished_at",
        "cpu_seconds",
        "gpu_held_seconds",
        "input_token_count",
        "output_token_count",
        "bias_hash",
        "whole_body_intervals",
        "keep_mask",
        "absolute_positions",
        "failures",
        "fallback_reasons",
        "oracle_checker_results",
    }
    assert required <= set(records[0])
    assert records[0]["output"] == "raw" and records[0]["attempted_tool_calls"] == [
        "call1"
    ]
    assert records[0]["classifier_decisions"][0]["verdict"] == "ABSTAIN"
    assert records[1]["tool_results"] == [{"result": 42}]
    assert "tool fact" in captured[0].text and "42" in captured[0].text
    assert captured[0].history_messages
    before = s.journal.path.read_bytes()
    with pytest.raises(ValueError):
        s.journal.append({"output": "incomplete"})
    assert s.journal.path.read_bytes() == before


def test_package_import_and_fake_decoder(tmp_path):
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location(
        "stencil_custom_generate",
        root / "models/stencil-package/custom_generate/generate.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    s = session(tmp_path)
    assert module.generate(session=s, decoder=lambda r: "CPU")[0] == "CPU"
    manifest = json.loads((root / "models/stencil-package/MANIFEST.json").read_text())
    assert manifest["actuator"]["default"] == "off"
    assert not manifest["actuator"]["enabled"]


def test_nested_defaults_and_reinstatement_tombstone():
    global_default = entry(role="system", eid="d", value="4")
    task_default = entry(role="system", eid="dt", value="8", scope=Scope("A"))
    r = Register(defaults=(global_default, task_default), task_handles={"A", "B"})
    assert r.live("A", "prose")[0].entry.value == "8"
    assert r.live("B", "prose")[0].entry.value == "4"
    r = r.apply(
        [
            entry(),
            entry("cancels", target=1, eid="c"),
            entry("reinstates", target=1, eid="r"),
        ]
    )
    rendered = render(r, Request("x", "prose", "A"))
    assert "replaced by indent v2" in rendered.tombstones[0]
    assert "reinstated as a new version" in rendered.tombstones[0]


def test_loop_transaction_and_overflow_never_call_decoder(tmp_path):
    s = session(tmp_path)
    calls = []
    with pytest.raises(InvalidEntry):
        generate_once(
            s,
            [message(entry()), message(entry("cancels", target=9, eid="c"))],
            lambda r: calls.append(r),
        )
    assert s.register == register() and not calls
    s.request = replace(
        s.request, max_tokens=1, encode=lambda text: tuple(text.encode())
    )
    with pytest.raises(RenderOverflow):
        generate_once(s, [], lambda r: calls.append(r))
    assert not calls
    assert len(s.journal.path.read_text().splitlines()) == 2


@pytest.mark.parametrize(
    "mode,needs_old", [("off", False), ("js_bias_mask", False), ("mask_only", True)]
)
def test_actuator_off_or_fallback(tmp_path, mode, needs_old):
    h = Hook()
    s = session(tmp_path, actuator_hook=h)
    s.request = replace(s.request, needs_old_body=needs_old)
    assert generate_once(s, [], lambda r: "once", actuator=mode)[0] == "once"
    assert h.restored == 0 and not h.active
    record = json.loads(s.journal.path.read_text())
    assert bool(record["fallback_reasons"]) == (mode != "off")


def test_historical_tombstones_and_literal_tokens_survive_expiry(tmp_path):
    s = session(tmp_path)
    s.request = replace(s.request, encode=lambda text: tuple(text.encode()))
    s.register = s.register.apply([entry(), entry("cancels", target=1, eid="c")])
    captured = []
    for _ in range(4):
        generate_once(
            s,
            [],
            lambda r: (
                captured.append(r)
                or DecodeResult("literal", tuple(b"literal"), None, True)
            ),
        )
    assert not captured[-1].tombstones
    assert "Retired: indent v1" in captured[-1].history_messages[0]["text"]
    assert b"Retired: indent v1" in bytes(captured[-1].prompt_ids)
    assert b"literal<|im_end|>\n" in bytes(s.history_ids)
