"""Rebuild DEV CPU consumer from literal saved outputs; no model or benchmark IO."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import sys
ROOT=Path('/home/bmarti44/stencil-llm');sys.path.insert(0,str(ROOT))
OUT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('pilot3_run',OUT/'run.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
p,slab=runner.p,runner.slab
from stencil.focus.loop import DecodeResult
from stencil.focus.journal import FIELDS

def lines(path):return [json.loads(s) for s in path.read_text().splitlines()] if path.exists() else []
def normalized(x):return json.loads(json.dumps(x))
def main():
    reg=json.loads((OUT/'registration.json').read_text())
    for name,digest in reg['source_hashes'].items():
        path=ROOT/name
        if path==OUT/'README.md' and (OUT/'prewritten.md').exists():path=OUT/'prewritten.md'
        assert p.sha(path)==digest,name
    rows=lines(OUT/'records.jsonl');http=lines(OUT/'http/records.jsonl')
    pairs={}
    for h in http:
        assert h['complete'] and h['done']
        ids=h['output_token_ids'];assert 0<len(ids)<=512
        assert h['usage']['completion_tokens']==len(ids)
        assert h['usage']['prompt_tokens']==len(h['prompt_token_ids'])
        assert not any(i in (151645,151643) for i in ids[:-1])
        assert (h['finish_reason']=='stop' and ids[-1] in (151645,151643)) or (h['finish_reason']=='length' and len(ids)==512)
        if h['pass_name']=='pilot':
            key=(h['index'],h['arm'],h['round'],runner.ids_hash(h['prompt_token_ids']))
            assert key not in pairs; pairs[key]=h
    assert len(pairs)==len(rows)
    grouped={}
    for r in rows:
        assert set(r)==FIELDS and not r['failures'] and not r['fallback_reasons']
        assert r['actuator']=='off' and r['experimental_flag_state']['applied']=='off'
        d=r['oracle_checker_results'][0];m=d['measurements']
        assert d['episode'].startswith('slab-dev-') and not d['hidden']
        key=(m['wave'],d['arm'],d['round'],m['prompt_sha256']);h=pairs[key]
        ids=r['output_token_ids']+([] if r['eos'] is None else [r['eos']])
        assert h['output_token_ids']==ids
        assert h['prompt_token_ids']==r['rendered_token_ids']
        assert runner.ids_hash(ids)==m['output_sha256']
        assert runner.ids_hash(r['rendered_token_ids']+ids)==m['transcript_sha256']
        assert (r['eos'] is None)==r['truncated']
        assert r['input_token_count']==len(r['rendered_token_ids'])<=32768-512
        assert r['output_token_count']==len(r['output_token_ids'])
        assert d['paired_gate']['allowed']
        grouped.setdefault((d['episode'],d['arm']),[]).append(r)
    checked=0
    with tempfile.TemporaryDirectory() as temp:
        for (episode,arm),saved in grouped.items():
            e=slab.generate_episode('dev',int(episode.rsplit('-',1)[1]))
            lane=p.Lane(Path(temp),e,arm,'audit')
            for r in sorted(saved,key=lambda r:r['oracle_checker_results'][0]['round']):
                d=r['oracle_checker_results'][0];index=d['round']
                assert index==len(lane.rows)
                lane.prepare(index);lane.gate=d['paired_gate'];lane.measurement={}
                def decode(req):
                    assert list(req.prompt_ids)==r['rendered_token_ids']
                    assert req.text==r['rendered_messages']
                    return p.tool_calls(DecodeResult(r['output'],tuple(r['output_token_ids']),r['eos'],r['truncated']))
                result=runner.one(lane,decode)
                fresh=result['oracle_checker_results'][0]
                assert fresh['outcome']==d['outcome'],(episode,arm,index,'outcome')
                for key in ('executed','results','tolerances'):
                    assert normalized(fresh['execution'][key])==d['execution'][key],(episode,arm,index,key)
                assert fresh['artifact_hashes']==d['artifact_hashes']
                for key in ('source_events','before_versions','after_versions','before_live_mask','after_live_mask','register_events','event_generations','defaults','applicability','executed_tool_calls','tool_results','artifact_hashes'):
                    assert normalized(result[key])==r[key],(episode,arm,index,key)
                checked+=1
            final=OUT/'c4'/episode/arm/'final-transcript.json'
            if final.exists():
                f=json.loads(final.read_text());assert f['ids']==list(lane.session.history_ids)
                assert f['sha256']==runner.ids_hash(f['ids'])
    det=json.loads((OUT/'determinism.json').read_text())
    first=[r for r in http if r['pass_name']=='b1_cold']
    assert len(first)==8
    for a in first:
        for mode in ('b1_warm','b4_mixed'):
            b=next(r for r in http if (r['pass_name'],r['index'])==(mode,a['index']))
            assert a['output_token_ids']==b['output_token_ids']
    assert det['passed'] and det['D']==0
    run=json.loads((OUT/'run.json').read_text())
    assert run['gpu_held_seconds']+json.loads((OUT/'initial-attempt/run.json').read_text())['gpu_held_seconds']<=9000
    assert run['stop']['returncode']==run['remove']['returncode']==0
    inspection=json.loads((OUT/'container-inspect.json').read_text())[0]
    assert inspection['Image']=='sha256:ffa30d66ff5c9346c6389507cc529827fc9934a6d2ee37855934f94fe1061cdc'
    assert not inspection['State']['Running']
    assert not (OUT/'RUNNING.flag').exists()
    p.write(OUT/'audit.json',dict(passed=True,records=checked,http_calls=len(http),
        exact_prompt_and_state_replays=checked,execution_and_checker_replays=checked,
        source_hashes=len(reg['source_hashes']),dev_only=True,hidden_capture=False,
        image_verified=True,cleanup_verified=True,determinism_verified=True))
    print('PASS',checked,'exact CPU trajectory replays')
if __name__=='__main__':main()
