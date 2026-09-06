"""SLAB CPU contracts; evaluation content is never printed or snapshotted."""

import json
from dataclasses import asdict
from pathlib import Path

import pytest

from stencil.focus.register import Register
from stencil.focus.slab import (
    DOMAINS,
    Executor,
    InvalidProgram,
    bank,
    check,
    digest,
    dry_run,
    evaluate,
    generate_episode,
    materialize,
    mutants,
    qwen_encode,
    reference,
    should_pass,
    tokenizer_manifest,
    write_manifests,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_determinism_disjointness_and_pressure_structure():
    dev, evaluation = bank(), bank("eval")
    assert [e.manifest() for e in dev] == [e.manifest() for e in bank()]
    assert len(dev) >= 8 and len(evaluation) == 64
    assert [len(e.turns) for e in evaluation].count(16) == 48
    assert [len(e.turns) for e in evaluation].count(32) == 16
    assert {e.seed for e in dev}.isdisjoint(e.seed for e in evaluation)
    assert {e.template_id for e in dev}.isdisjoint(e.template_id for e in evaluation)
    assert {e.domain for e in dev} == set(DOMAINS)
    assert digest(asdict(dev[0])) != digest(asdict(generate_episode(seed=17)))
    for e in (*dev, *evaluation):
        state = Register(defaults=e.defaults, task_handles={"A", "B"})
        events = []
        switches = sum(
            a.task != b.task for a, b in zip(e.turns, e.turns[1:], strict=False)
        )
        assert 2 <= switches <= 3
        assert any(t.task == "A" for t in e.turns[5:])
        for t in e.turns:
            state = state.apply(t.events)
            assert {
                v.entry.key: v.entry.value for v in state.live(t.task, "tool_call")
            } == dict(t.live)
            assert 3 <= len(t.live) <= 5
            assert dict(t.live)["indent"] in {"2", "3", "4"}
            assert all(f"{k}={v}" in t.t_text for k, v in t.live)
            if t.index < 10:
                assert not t.retired
            assert not any(x == t.public_case for x, _ in e.private[t.index]["cases"])
            events.extend(t.events)
        assert {"supersedes", "cancels", "completes", "reinstates"} <= {
            x.action for x in events
        }
        assert any(dict(t.denominators)["style"] for t in e.turns)
        assert any(dict(t.denominators)["format"] for t in e.turns)
        assert any(dict(t.denominators)["process"] for t in e.turns)
        assert "private" not in e.public_view()
        assert all("expression" not in t for t in e.public_view()["turns"])


@pytest.mark.parametrize(
    "family,index", [("dev", i) for i in range(8)] + [("eval", i) for i in range(64)]
)
def test_every_reference_and_mutant_witness(tmp_path, family, index):
    e = generate_episode(family, index)
    # CPU checker audit is authorized; no evaluation content is sent to a decoder.
    materialize(e, tmp_path, e.manifest()["episode_sha256"])
    executor = Executor(
        tmp_path, json.loads((tmp_path / "public_tests.json").read_text())
    )
    seen = set()
    for i, _t in enumerate(e.turns):
        before = {p: (tmp_path / p).read_text() for p in ("core.py", "policy.py")}
        history = list(executor.prior_bodies)
        for label, output in mutants(e, i).items():
            executor.prior_bodies = list(history)
            for p, content in before.items():
                (tmp_path / p).write_text(content)
            executor.run(output)
            result = check(e, i, output, executor)
            group, kind = (
                ("relapse", label.split(":")[1])
                if ":" in label
                else ("violations", label)
            )
            if label == "hidden_only":
                kind = "semantic"
                assert executor.results[-1]["failed"] == 0
                assert executor.results[-1]["passed"] == i + 1
            assert result[group][kind], (e.episode_id, i, label)
            assert not result["success"]
            seen.add(label)
        for label, output in should_pass(e, i).items():
            executor.prior_bodies = list(history)
            for p, content in before.items():
                (tmp_path / p).write_text(content)
            executor.run(output)
            result = check(e, i, output, executor)
            assert result["success"], (e.episode_id, i, label, result)
        executor.prior_bodies = list(history)
        for p, content in before.items():
            (tmp_path / p).write_text(content)
        output = reference(e, i)
        feedback = executor.run(output)
        result = check(e, i, output, executor)
        assert result["success"], (e.episode_id, i, result)
        assert len(feedback["executed"]) == 3
        assert feedback["results"][-1]["passed"] == i + 1
        assert not any(result["relapse"].values())
    assert {"relapse:style", "relapse:format", "relapse:process"} <= seen
    assert result["integration"]


def test_manifest_hashes(tmp_path):
    receipt = write_manifests(tmp_path)
    frozen = json.loads((FIXTURES / "slab_manifest.json").read_text())
    assert receipt == frozen
    audit = json.loads((FIXTURES / "slab_cpu_audit.json").read_text())
    assert audit["freeze"] == {key: receipt[key] for key in audit["freeze"]}
    assert audit["own_body_tokens"]["in_100_300"] == 1440
    assert audit["own_body_tokens"]["first_ten_eligible_episodes"] == 72
    assert max(audit["max_context_tokens"].values()) + 512 <= 32768
    assert receipt == json.loads((tmp_path / "slab_manifest.json").read_text())
    assert len(receipt["oracle_text_subset"]) == 16
    # Stratify by domain as well as episode length, not index modulo four.
    subset = receipt["oracle_text_subset"]
    assert len(set(subset)) == 16
    chosen = [e for e in bank("eval") if e.episode_id in subset]
    assert {e.domain for e in chosen} == set(DOMAINS)
    assert {len(e.turns) for e in chosen} == {16, 32}
    for family in ("dev", "eval"):
        for e, manifest in zip(bank(family), receipt["banks"][family], strict=False):
            assert manifest["episode_sha256"] == digest(asdict(e))
            assert manifest["public_sha256"] == digest(e.public_view())
            assert manifest["hidden_sha256"] == digest(e.private)


def test_dev_loop_dry_run(tmp_path):
    result = dry_run(tmp_path)
    frozen = json.loads((FIXTURES / "slab_dev_golden.json").read_text())
    for key in ("accounting", "rendered_sha256", "events_sha256", "final_hashes"):
        assert result[key] == frozen[key]
    rows = [json.loads(x) for x in (tmp_path / "loop.jsonl").read_text().splitlines()]
    checks = [
        json.loads(x) for x in (tmp_path / "checker.jsonl").read_text().splitlines()
    ]
    assert len(rows) == len(checks) == 16
    for i, (row, checker) in enumerate(zip(rows, checks, strict=False)):
        assert row["request_id"] == i
        assert checker["outcome"]["success"]
        assert row["attempted_tool_calls"] == checker["executed"]["executed"]
        assert row["executed_tool_calls"] == (
            checks[i - 1]["executed"]["executed"] if i else []
        )
        assert row["tool_results"] == (
            checks[i - 1]["executed"]["results"] if i else []
        )
        assert row["gpu_held_seconds"] == 0
    assert result["model_cost_projection"] is None
    assert result["tokenizer"] == tokenizer_manifest()
    assert result["own_body_counts"]["first_ten_100_300"] == 10
    assert result["accounting"][-1]["prompt"] > result["accounting"][0]["prompt"]
    with pytest.raises(ValueError, match="freeze"):
        dry_run(tmp_path / "eval", generate_episode("eval"))


def test_fail_closed_bounds_scope_receipts_and_missingness(tmp_path):
    e = generate_episode()
    with pytest.raises(ValueError, match="freeze"):
        materialize(generate_episode("eval"), tmp_path)
    materialize(e, tmp_path)
    ex = Executor(tmp_path, json.loads((tmp_path / "public_tests.json").read_text()))
    malformed = json.loads(reference(e, 0))
    malformed["calls"][1]["path"] = "../escape.py"
    ex.run(json.dumps(malformed))
    assert check(e, 0, json.dumps(malformed), ex)["violations"]["breakage"]
    assert not (tmp_path.parent / "escape.py").exists()
    ex.run(reference(e, 0))
    # A receipt from a different workspace state cannot authorize delivery.
    (tmp_path / "policy.py").write_text("# tampered\n")
    assert check(e, 0, reference(e, 0), ex)["violations"]["process"]
    missing = check(e, 12, "", ex, executed=False)
    assert missing["relapse"] is None and not missing["observed"]
    assert missing["denominators"] == dict(e.turns[12].denominators)
    for code in (
        "import os",
        'def f(x):\n    return __import__("os")',
        "def f(x):\n    while True: pass",
        "def f(x):\n    return 2 ** 999999999",
    ):
        with pytest.raises(InvalidProgram):
            evaluate(code, "f", list(range(65)))


def test_paired_clauses_have_no_absolute_floor_and_do_not_reward_missingness():
    import copy

    from stencil.focus.slab import paired_clauses

    # R40/N12 is informative despite both missing the old absolute product floor.
    clean = dict(
        observed=True,
        denominators=dict(language=0, style=1, format=0, process=0),
        relapse=dict(language=False, style=False, format=False, process=False),
        violations=dict(breakage=False),
        success=True,
    )
    r = [[copy.deepcopy(clean) for _ in range(16 if i < 48 else 32)] for i in range(64)]
    n = copy.deepcopy(r)
    for i in range(64):
        r[i][-1]["success"] = i < 40
        n[i][-1]["success"] = i < 12
    result = paired_clauses(r, n)
    assert result["clauses_pass"] and result["gain"] == 28
    n[0][11].update(observed=False, relapse=None, violations=None)
    result = paired_clauses(r, n)
    assert not result["complete"] and not result["clauses_pass"]
    assert result["common_opportunities"]["style"]["missing"] == 1
    n[0][11] = copy.deepcopy(clean)
    r[0][11]["relapse"]["style"] = True
    assert not paired_clauses(r, n)["relapse_clause"]
    r[0][11]["relapse"]["style"] = False
    r[0][1]["violations"]["breakage"] = True
    assert paired_clauses(r, n)["breakage_clause"]
    r[1][1]["violations"]["breakage"] = True
    assert not paired_clauses(r, n)["breakage_clause"]


def test_strict_template_schedule_and_rule_disjointness():
    import re

    dev, evaluation = bank(), bank("eval")

    def scaffolds(episodes):
        # Remove lifecycle announcements and variable problem data, preserving
        # the actual repeated instruction production, not a family/template ID.
        return {
            re.sub(r"\d+", "#", t.request.split(". ", 1)[1].split("Public")[0])
            for e in episodes
            for t in e.turns
        }

    def schedules(episodes):
        return {
            tuple(
                (
                    t.index,
                    x.action,
                    x.key,
                    x.value,
                    x.scope.task_handle,
                    x.target_version,
                )
                for t in e.turns
                for x in t.events
                if t.index > 0
            )
            for e in episodes
        }

    def rules(episodes):
        return {
            x.text
            for e in episodes
            for x in (*e.defaults, *(x for t in e.turns for x in t.events))
        }

    assert scaffolds(dev).isdisjoint(scaffolds(evaluation))
    assert schedules(dev).isdisjoint(schedules(evaluation))
    assert rules(dev).isdisjoint(rules(evaluation))
    shapes = {
        tuple(
            x.key
            for t in e.turns
            if t.index > 0
            for x in t.events
            if x.action in {"supersedes", "completes"}
            or (x.action == "cancels" and x.key == "format")
        )
        for e in evaluation
    }
    assert len(shapes) >= 6
    assert {
        x.key
        for e in evaluation
        for t in e.turns
        for x in t.events
        if x.action == "supersedes"
    } == {"indent", "format"}
    assert {
        x.key
        for e in evaluation
        for t in e.turns
        for x in t.events
        if x.action == "completes"
    } == {"delivery", "format"}
    assert len(schedules(evaluation)) >= 48
    for e in (*dev, *evaluation):
        completed = next(
            t.index
            for t in e.turns
            if any(x.action == "completes" and x.key == "delivery" for x in t.events)
        )
        assert (
            sum(dict(t.denominators)["process"] for t in e.turns[completed + 1 :]) >= 3
        )


def test_python_specificity_and_repair(tmp_path):
    assert evaluate(
        "def f(x):\n    return [ord(x), pow(2, 3), divmod(7, 2), next(iter([9]))]",
        "f",
        "a",
    ) == [97, 8, [3, 1], 9]

    assert evaluate(
        'def f(x: list):\n    """Ordinary Python idioms."""\n    y = sorted(list(x))\n'
        "    return (max(abs(v) for v in y), min(y),"
        " any(v in (2, 3) for v in y), all(v // 2 >= -2 for v in y))",
        "f",
        [-3, 2],
    ) == [3, -3, True, True]
    assert (
        evaluate(
            "def f(x):\n    return sum(v for v in x)\n\ndef f(x):\n    return len(x)",
            "f",
            [1, 2],
        )
        == 2
    )
    e = generate_episode()
    materialize(e, tmp_path)
    executor = Executor(
        tmp_path, json.loads((tmp_path / "public_tests.json").read_text())
    )
    payload = json.loads(reference(e, 0))
    broken = json.loads(reference(e, 0))
    broken["calls"][1]["code"] = "def broken(:\n"
    executor.run(json.dumps(broken))
    assert check(e, 0, json.dumps(broken), executor)["violations"]["breakage"]
    payload["calls"][1]["op"] = "replace"
    payload["calls"][1]["code"] = (
        dict(e.initial)[e.turns[0].path] + payload["calls"][1]["code"]
    )
    # Existing code is retained at its old indentation; style checks only new
    # function AST regions in the replacement (see separate mixed-style test).
    payload["calls"][1]["code"] = json.loads(reference(e, 0))["calls"][1]["code"]
    executor.run(json.dumps(payload))
    assert check(e, 0, json.dumps(payload), executor)["success"]


def test_no_prior_trait_means_no_relapse(tmp_path):
    e = generate_episode()
    materialize(e, tmp_path)
    executor = Executor(
        tmp_path, json.loads((tmp_path / "public_tests.json").read_text())
    )
    index = next(
        t.index for t in e.turns if any(x.action == "reinstates" for x in t.events)
    )
    for i in range(index):
        executor.run(reference(e, i))
    output = mutants(e, index)["relapse:style"]
    executor.prior_bodies = []
    executor.run(output)
    result = check(e, index, output, executor)
    assert result["attempted_relapse"]["style"]
    assert not result["prior_trait_present"]["style"]
    assert not result["relapse"]["style"]
    assert result["violations"]["style"]


def test_tokenizer_system_excerpt_and_transport(tmp_path):
    from stencil.focus.slab import SYSTEM_PROMPT, TOOL_SCHEMA, byte_encode

    assert "delivery ready" in SYSTEM_PROMPT
    assert "replace" in SYSTEM_PROMPT and "seccomp" in SYSTEM_PROMPT
    with pytest.raises(ValueError, match="real Qwen"):
        dry_run(tmp_path / "bytes", encode=byte_encode)
    e = generate_episode()
    materialize(e, tmp_path)
    executor = Executor(tmp_path, [])
    content = "# " + "x" * 2000 + "\n"
    (tmp_path / "core.py").write_text(content)
    result = executor.run(
        json.dumps({"calls": [{"op": "read", "path": "core.py"}], "report": {}})
    )["results"][0]
    assert result["excerpt"] == content[-TOOL_SCHEMA["max_read_bytes"] :]
    assert result["sha256"] == executor.hashes()["core.py"]
    assert result["bytes"] == len(content)
    assert all(100 <= len(qwen_encode(reference(e, i))) <= 300 for i in range(16))


def test_sandbox_kernel_denies_network_and_file_open():
    # Deliberately escape the convenience builtin restriction: the kernel policy
    # must still deny network and host reads. This opens no socket or host file.
    code = """def f(x):
    thread = next(c for c in object.__subclasses__() if c.__name__ == "Thread")
    modules = thread.__init__.__globals__["_sys"].modules
    ctypes = modules["ctypes"]
    libc = ctypes.CDLL(None, use_errno=True)
    network = libc.socket(2, 1, 0)
    network_errno = ctypes.get_errno()
    host_file = libc.open(b"/etc/passwd", 0)
    return [network, network_errno, host_file, ctypes.get_errno()]
"""
    assert evaluate(code, "f", None) == [-1, 1, -1, 1]


def test_paired_context_overflow_is_all_or_none():
    from stencil.focus.slab import paired_context_gate

    assert paired_context_gate(dict(R=32000, N=10000, T=11000, O=32000))
    assert not paired_context_gate(dict(R=32257, N=10000, T=11000, O=32000))
    with pytest.raises(ValueError, match="all four"):
        paired_context_gate(dict(R=100))


def test_transport_serializes_tool_result_once(tmp_path):
    from stencil.focus.journal import Journal
    from stencil.focus.loop import Message, Session, generate_once
    from stencil.focus.renderer import Request, compact

    result = ({"excerpt": "unique-tool-excerpt"},)
    session = Session(Register(), Request("", "tool_call"), Journal(tmp_path / "log"))
    seen = []
    generate_once(
        session,
        [Message("tool", "tool", compact(result), tool_results=result)],
        lambda rendered: seen.append(rendered.text) or "ok",
    )
    assert seen[0].count("unique-tool-excerpt") == 1


def test_tombstones_expire_and_rewrite_preserves_old_style(tmp_path):
    e = generate_episode()
    retired_at = {}
    for t in e.turns:
        for event in t.events:
            if event.action in {"supersedes", "cancels", "completes"}:
                retired_at[event.key] = t.index
        prose = t.t_text.split(". Not binding: ", 1)[1]
        for key, value in t.retired:
            assert (f"{key}={value}" in prose) == (t.index - retired_at[key] < 3)
    materialize(e, tmp_path)
    executor = Executor(
        tmp_path, json.loads((tmp_path / "public_tests.json").read_text())
    )
    changed = next(
        t.index for t in e.turns if any(x.action == "supersedes" for x in t.events)
    )
    for i in range(changed):
        executor.run(reference(e, i))
    output = should_pass(e, changed)["whole_file"]
    executor.run(output)
    result = check(e, changed, output, executor)
    assert result["success"]
    assert result["prior_trait_present"]["style"]
    assert not result["relapse"]["style"]
    assert check(e, changed, output, executor, truncated=True)["violations"]["breakage"]


def test_sandbox_network_filter_covers_watchdog_thread():
    code = """def f(x):
    thread = next(c for c in object.__subclasses__() if c.__name__ == "Thread")
    modules = thread.__init__.__globals__["_sys"].modules
    ctypes = modules["ctypes"]
    libc = ctypes.CDLL(None, use_errno=True)
    timers = [t for t in modules["threading"].enumerate()
              if isinstance(t, modules["threading"].Timer)]
    def probe():
        result = libc.socket(2, 1, 0)
        error = ctypes.get_errno()
        encoded = modules["json"].dumps({"values": [[result, error]]}).encode()
        modules["os"].write(1, encoded)
        modules["os"]._exit(0)
    timers[0].function = probe
    while True:
        modules["time"].sleep(0.01)
"""
    assert evaluate(code, "f", None) == [-1, 1]


@pytest.mark.parametrize("index", [0, 3])
def test_repair_unparsable_preserves_retired_style(tmp_path, index):
    e = generate_episode("dev", index)
    materialize(e, tmp_path)
    executor = Executor(
        tmp_path, json.loads((tmp_path / "public_tests.json").read_text())
    )
    turn = next(
        t.index
        for t in e.turns
        if any(
            event.action == "supersedes" and event.kind == "style" for event in t.events
        )
    )
    for i in range(turn):
        executor.run(reference(e, i))
    payload = json.loads(reference(e, turn))
    edit = next(c for c in payload["calls"] if c["op"] == "edit")
    path = edit["path"]
    previous = (tmp_path / path).read_text()
    executor.run(
        json.dumps(
            {
                "calls": [{"op": "edit", "path": path, "code": "\ndef broken(:\n"}],
                "report": {},
            }
        )
    )
    edit.update(op="replace", code=previous + edit["code"])
    output = json.dumps(payload)
    executor.run(output)
    result = check(e, turn, output, executor)
    assert result["prior_trait_present"]["style"]
    assert not result["attempted_relapse"]["style"]
    assert not result["relapse"]["style"]
    assert result["success"], result
    # A new stale definition remains a real violation after the repair.
    stale = json.loads(mutants(e, turn)["relapse:style"])
    executor.run(json.dumps(stale))
    result = check(e, turn, json.dumps(stale), executor)
    assert result["violations"]["style"] and result["relapse"]["style"]
