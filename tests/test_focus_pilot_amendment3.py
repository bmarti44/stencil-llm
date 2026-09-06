"""DEV-only consumer regressions for Amendment 3."""
import json
import subprocess
from pathlib import Path
import pytest
from stencil.focus import slab


def executor(tmp_path):
    e = slab.generate_episode('dev', 0)
    slab.materialize(e, tmp_path)
    return e, slab.Executor(tmp_path, json.loads((tmp_path/'public_tests.json').read_text()))


@pytest.mark.parametrize('tail', ['}', ']', ' } \n'])
def test_single_closer_executes_and_checks(tmp_path, tail):
    e, ex = executor(tmp_path)
    output = slab.reference(e, 0) + tail
    result = ex.run(output)
    assert len(result['executed']) == 3
    assert result['tolerances'] == [dict(tolerance='trailing_closer', closer=tail.strip())]
    assert slab.check(e, 0, output, ex)['success']


@pytest.mark.parametrize('tail', ['}}', '}]', ' true', ' garbage', '{}'])
def test_other_tails_rejected_with_reason(tmp_path, tail):
    e, ex = executor(tmp_path)
    output = slab.reference(e, 0) + tail
    result = ex.run(output)
    assert not result['executed']
    assert result['results'][0]['reason'] == 'unexpected trailing ' + json.dumps(tail.strip())
    assert slab.check(e, 0, output, ex)['violations']['breakage']


def test_task_letter_and_delivery_contract(tmp_path):
    e, ex = executor(tmp_path)
    good = json.loads(slab.reference(e, 0))
    assert good['report']['task'] == e.turns[0].task
    bad = dict(good, report=dict(good['report'], task=e.turns[0].request, delivery={'policy.py':'code'}))
    output = json.dumps(bad)
    ex.run(output)
    assert slab.check(e, 0, output, ex)['violations']['format']
    assert 'workshop LETTER "A" or "B"' in slab.SYSTEM_PROMPT
    assert '"task":"B","delivery":"staged"' in slab.SYSTEM_PROMPT
    assert 'never file content or an object' in slab.SYSTEM_PROMPT


def test_edit_feedback_preserves_function_list(tmp_path):
    e, ex = executor(tmp_path)
    for i in range(2):
        output = slab.reference(e, i)
        result = ex.run(output)
        edit = next(r for r in result['results'] if r.get('op') == 'edit')
        names = edit['functions']
        assert e.turns[i].function in names
        assert len(names) == len(set(names))
        assert slab.check(e, i, output, ex)['success']
    assert 'Append only the new function; never re-emit earlier functions.' in slab.SYSTEM_PROMPT


def test_size_guard_uses_staged_blob(tmp_path):
    hook = Path(__file__).resolve().parents[1]/'tools/hooks/pre-commit'
    def git(*args):
        return subprocess.run(['git', *args], cwd=tmp_path, check=True, capture_output=True)
    git('init')
    target = tmp_path/'file with spaces'
    target.write_bytes(b'x' * 10_000_000)
    git('add', '--', target.name)
    assert subprocess.run([str(hook)], cwd=tmp_path).returncode == 0
    target.write_bytes(b'x' * 10_000_001)
    git('add', '--', target.name)
    target.write_text('small worktree cannot conceal large staged blob')
    assert subprocess.run([str(hook)], cwd=tmp_path).returncode == 1
