"""CPU regressions for the registered arm-neutral harness fixes."""

import json
from pathlib import Path

import pytest

from stencil.focus.register import Register
from stencil.focus.renderer import Request, render, value_gloss
from stencil.focus.slab import Executor, check, generate_episode, materialize, reference


@pytest.mark.parametrize("before", ["", "# old", "# old\n"])
@pytest.mark.parametrize("op", ["edit", "replace"])
def test_boundary_and_exact_replacement(tmp_path, before, op):
    (tmp_path / "core.py").write_text(before)
    (tmp_path / "policy.py").write_text("")
    ex = Executor(tmp_path, [])
    code = "def f():\n   return 1"
    result = ex.run(
        json.dumps(dict(calls=[dict(op=op, path="core.py", code=code)], report={}))
    )
    prefix = before + ("\n" if before and not before.endswith("\n") else "")
    assert (tmp_path / "core.py").read_text() == (prefix if op == "edit" else "") + code
    assert len(result["executed"]) == 1
    assert ex.emitted_codes == [code]


def test_separator_counts_toward_byte_bound(tmp_path):
    (tmp_path / "core.py").write_text("#" * 65535)
    (tmp_path / "policy.py").write_text("")
    ex = Executor(tmp_path, [])
    result = ex.run(
        json.dumps(dict(calls=[dict(op="edit", path="core.py", code="x")], report={}))
    )
    assert result["results"] == [dict(error="edit bound")]
    assert (tmp_path / "core.py").stat().st_size == 65535


def test_reference_without_trailing_newlines_integrates(tmp_path):
    e = generate_episode("dev", 0)
    materialize(e, tmp_path)
    ex = Executor(tmp_path, json.loads((tmp_path / "public_tests.json").read_text()))
    for i in range(16):
        output = json.loads(reference(e, i))
        for call in output["calls"]:
            if call["op"] == "edit":
                call["code"] = call["code"].rstrip("\n")
        text = json.dumps(output)
        ex.run(text)
        outcome = check(e, i, text, ex)
        assert outcome["success"] and outcome["integration"], (i, outcome)


@pytest.mark.parametrize("arm", ["R", "N", "T", "O"])
def test_gloss_reaches_each_arm_on_add_and_supersede(arm):
    e = generate_episode("dev", 0)
    register = Register(defaults=e.defaults, task_handles={"A", "B"})
    seen = set()
    for turn in e.turns:
        register = register.apply(turn.events)
        out = render(
            register,
            Request(
                turn.request,
                "tool_call",
                turn.task,
                rule_mode=arm,
                rule_text=turn.t_text,
            ),
        )
        for event in turn.events:
            if event.kind == "style":
                assert value_gloss("style", event.value).strip() in out.text
                seen.add(event.action)
    assert {"add", "supersedes"} <= seen
    assert value_gloss("format", "3") == ""


@pytest.mark.parametrize("literal", ["True", "False"])
def test_python_literals_remain_rejected(tmp_path, literal):
    e = generate_episode("dev", 0)
    materialize(e, tmp_path)
    ex = Executor(tmp_path, [])
    text = '{"calls":[],"status":"ok","verbose":' + literal + "}"
    result = ex.run(text)
    assert not result["executed"] and not result["tolerances"]
    assert result["results"][0]["error"] == "envelope"


@pytest.mark.parametrize("arm", ["R", "N", "T", "O"])
def test_cap_is_breakage_for_every_arm(tmp_path, arm):
    e = generate_episode("dev", 0)
    materialize(e, tmp_path)
    ex = Executor(tmp_path, json.loads((tmp_path / "public_tests.json").read_text()))
    output = reference(e, 0)
    ex.run(output)
    assert check(e, 0, output, ex, truncated=True)["violations"]["breakage"]


def test_registered_backend_and_compliance_gates():
    readme = (
        (
            Path(__file__).resolve().parents[1]
            / "results/quick-checks/composition-pilot-2/README.md"
        )
        .read_text()
        .split("## Amendment 2")[1]
    )
    for requirement in (
        "outcome-blind",
        "supersedes the registered <=1-divergence gate",
        "cold/warm single-stream",
        "mixed-arm concurrency 4, D=0",
        "151645",
        "cap 512",
        "32,768",
        "first positions",
        "controller/register/renderer/checker/executor hashes",
        "package path outcome-unvalidated",
        "teacher-forced prefill",
        "round-0 compliance",
        "swap the style trait",
    ):
        assert requirement in readme
