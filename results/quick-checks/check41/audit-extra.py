"""Additional read-only reconstruction audit; writes only its check41 audit receipt."""
import hashlib
import importlib.util
import json
import subprocess
from collections import Counter
from pathlib import Path

import torch
from transformers import AutoTokenizer

ROOT = Path('/home/bmarti44/stencil-llm')
OUT = ROOT / 'results/quick-checks/check41'
spec = importlib.util.spec_from_file_location('check41_audit_target', ROOT / 'scripts/focus_check41.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
rows = [json.loads(line) for line in (OUT / 'records.jsonl').read_text().splitlines()]
summary = json.loads((OUT / 'summary.json').read_text())
assert summary['complete'] and len(rows) == 2528
assert Counter(r['phase'] for r in rows) == dict(competence=96, profile=64, grid=384, fresh_default=64, screen=1920)
assert len({(r['phase'], r['arm'], r['step'], r['episode']) for r in rows}) == len(rows)
banks = json.loads((OUT / 'banks.json').read_text())
assert banks == m.bank()
tasks = {t['id']: t for split in banks.values() for t in split}
tasks['neutral'] = dict(id='neutral', prompt='Reply only OK.', name='', witness='')
runtime = json.loads((OUT / 'runtime.json').read_text())
eos = set(runtime['eos'])
tokenizer = AutoTokenizer.from_pretrained(ROOT / 'models/qwen3-4b-hf', local_files_only=True)
for r in rows:
    ids = m.encode_messages(tokenizer, r['history'])
    assert ids == r['input_token_ids']
    assert hashlib.sha256(json.dumps(ids).encode()).hexdigest() == r['input_sha256']
    assert tokenizer.decode(r['generated_token_ids'], skip_special_tokens=True) == r['text']
    assert bool(r['generated_token_ids'][-1] in eos) == r['eos']
    assert not any(t in eos for t in r['generated_token_ids'][:-1])
    assert r['truncated'] == (not r['eos'] and len(r['generated_token_ids']) >= m.CAP)
    assert not r['cost_stopped']
    assert r['history'][0] == dict(role='system', content=m.base.SYSTEM)
    task = tasks[r['task_id']]
    assert r['history'][-1] == dict(role='user', content=task['prompt'] + (f" Use {r['cue']}." if r['cue'] else ''))
    if r['phase'] != 'screen':
        assert len(r['history']) == 2
    if r['step'] == 'NEUTRAL':
        assert r['score'] == dict(neutral_ok=r['text'].strip() == 'OK')
for e in range(64):
    indices = dict(zip(('SET','HOLD','SWITCH','BACK','CLEAR'), ((e+k)%64 for k in (0,13,26,39,52)), strict=True))
    for arm in m.ARMS:
        rs = [r for r in rows if r['phase']=='screen' and r['episode']==e and r['arm']==arm]
        assert [r['step'] for r in rs] == list(m.STEPS)
        history = [dict(role='system', content=m.base.SYSTEM)]
        for r in rs:
            step = r['step']
            task = tasks['neutral'] if step=='NEUTRAL' else banks['screen'][indices[step]]
            assert r['task_id'] == task['id']
            cue = m.TARGETS[step] if arm=='text-cue' and step!='NEUTRAL' else None
            assert r['cue'] == cue
            assert r['history'] == m.base.messages_for(task, cue=cue, history=history)
            assert r['scaling_active'] == (arm in ('correct','swapped','shuffled') and step!='CLEAR')
            history = r['history'] + [dict(role='assistant', content=r['text'])]
for lang in m.LANGS:
    rs = [r for r in rows if r['phase']=='competence' and r['arm']==lang]
    expected = dict(n=32, valid=sum(r['score']['valid_language']==lang for r in rs),
        task_check=sum(r['score']['valid_language']==lang and r['score']['valid_task'] for r in rs))
    assert summary['competence'][lang] == expected
assert summary['competence']['default'] == dict(Counter(r['score']['valid_language'] or 'broken' for r in rows if r['phase']=='competence' and r['arm']=='OFF'))
assert [r['phase'] for r in rows] == ['competence']*96 + ['profile']*64 + ['grid']*384 + ['fresh_default']*64 + ['screen']*1920
sets = json.loads((OUT / 'neuron-sets.json').read_text())
grid = json.loads((OUT / 'grid.json').read_text())
assert grid['frozen'] and grid['screen_records_at_freeze']==0
assert grid['selected'] == m.choose_grid(grid['cells'])
chosen = grid['selected']
frozen = torch.load(OUT / 'frozen-scales.pt', weights_only=True)
assert frozen['selected'] == chosen
for arm in ('correct','shuffled'):
    expected = m.scales(sets[arm][str(chosen['k'])], sets['shape'], chosen['gain'], chosen['variant'])
    assert torch.equal(frozen[arm], expected)
freeze = json.loads((OUT / 'freeze.json').read_text())
launch = json.loads((OUT / 'launch.json').read_text())
for name, digest in freeze['files'].items():
    assert m.sha(ROOT/name) == digest
    assert subprocess.check_output(['git','-C',str(ROOT),'show',launch['git_head']+':'+name]) == (ROOT/name).read_bytes()
assert launch['freeze_sha256'] == m.sha(OUT/'freeze.json') == summary['freeze_sha256']
assert summary['records_sha256'] == m.sha(OUT/'records.jsonl')
prior = json.loads((OUT/'attempt1/summary.json').read_text())
assert (OUT/'attempt1/records.jsonl').stat().st_size == 0 and prior['record_count']==0
assert prior['gpu_seconds'] == summary['prior_attempt_gpu_seconds'] == json.loads((OUT/'prior-attempts.json').read_text())['gpu_seconds']
assert abs(summary['gpu_seconds']-summary['prior_attempt_gpu_seconds']-summary['current_attempt_gpu_seconds']) < 1e-8
assert summary['gpu_seconds'] >= sum(r['seconds'] for r in rows) + runtime['load_seconds'] + prior['gpu_seconds']
assert summary['gpu_seconds'] <= 7200 and summary['cap_overrun_seconds']==0
assert not torch.cuda.is_initialized()
m.write_json(Path('/tmp/stencil-check41-audits/audit-extra.json'),dict(passed=True,records=len(rows),episodes=64,
    token_ids_text_and_hashes_exact=True,all_history_pairs_exact=True,
    arm_cues_and_scaling_flags_exact=True,competence_recomputed=True,
    phase_order_exact=True,frozen_scales_recomputed=True,
    launch_commit_bytes_verified=True,prior_empty_attempt_charged=True,
    cuda_initialized=False,records_sha256=m.sha(OUT/'records.jsonl')))
print('Additional token/history/freeze/cost audit passed for all 2528 records.',flush=True)
