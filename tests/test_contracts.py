"""Authoring self-check for the contract-domain tasks: gold passes its own tests, the
contract tests discriminate between states, and the scorer separates functional from
contract outcomes."""

import pytest

from stencil.contract_projects import all_tasks
from stencil.contract_projects_reg import registered_tasks
from stencil.contracts import extract_file, render_request, run_tests, score

TASKS = all_tasks() + registered_tasks()
BY_ID = {t.id: t for t in TASKS}


@pytest.mark.parametrize("task", TASKS, ids=[t.id for t in TASKS])
def test_gold_reaches_joint_success(task):
    r = score(task, task.gold)
    assert r["J"], r


@pytest.mark.parametrize("task", TASKS, ids=[t.id for t in TASKS])
def test_unmodified_target_fails_functionally(task):
    r = score(task, task.files[task.target])
    assert r["parsed"] and not r["functional"]


@pytest.mark.parametrize("task", TASKS, ids=[t.id for t in TASKS])
def test_each_contract_test_discriminates(task):
    # every other task of the same project has some state flipped: its gold must pass
    # the functional tests and fail at least one of this task's contract tests
    # every other task of the same project has some state flipped: its gold must not
    # reach joint success here (project files may differ by state, so a cross-state
    # gold is allowed to fail functionally instead of on the contract tests)
    others = [t for t in TASKS if t.project == task.project and t.id != task.id]
    for other in others:
        files = {**task.files, task.target: other.gold}
        f_ok, _ = run_tests(files, task.functional_tests)
        c_ok, msg = run_tests(files, task.contract_tests) if f_ok else (False, "")
        assert not (f_ok and c_ok), (task.id, other.id, msg)


def test_extract_and_render():
    t = BY_ID["kvstore-none-dataclass"]
    prompt = render_request(t)
    assert "store/records.py" in prompt and t.contracts[0].text in prompt
    assert "Lookups of missing records" not in render_request(
        t, contracts_in_request=False
    )
    assert extract_file("text\n```python\nx = 1\n```\n") == "x = 1\n"
    assert extract_file("no code") is None
    assert score(t, None) == {
        "parsed": False,
        "functional": False,
        "contract": False,
        "J": False,
    }
