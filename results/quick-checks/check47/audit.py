"""Rebuild DEV CPU consumer from literal saved outputs; no model or benchmark IO."""
import importlib.util
import io, tarfile
import atexit
import json
from pathlib import Path
import subprocess
import tempfile
import sys
ROOT=Path('/home/bmarti44/stencil-llm');sys.path.insert(0,str(ROOT))
OUT=Path(__file__).resolve().parent
# Concurrent work changed live sources after the recipe freeze. Replay only the
# committed recipe tree; leave the shared worktree untouched.
_snapshot=tempfile.TemporaryDirectory(prefix='check47-audit-');atexit.register(_snapshot.cleanup)
SNAP=Path(_snapshot.name)
with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','-C',str(ROOT),'archive','184cb321','src','scripts']))) as tar:tar.extractall(SNAP,filter='data')
sys.path[:0]=[str(SNAP/'src'),str(SNAP),str(SNAP/'scripts')]
import stencil.focus, scripts
from scripts import composition_pilot

spec=importlib.util.spec_from_file_location('pilot3_run',ROOT/'results/quick-checks/composition-pilot-4/run.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
p,slab=runner.p,runner.slab
slab.TOKENIZER_PATH=Path("/home/bmarti44/models/qwen3.8-27b-fp8/tokenizer.json");slab.qwen_tokenizer.cache_clear()
from stencil.focus.loop import DecodeResult
from stencil.focus.journal import FIELDS

def lines(path):return [json.loads(s) for s in path.read_text().splitlines()] if path.exists() else []
def normalized(x):return json.loads(json.dumps(x))
def main():
    phases=[OUT]+([OUT/'continuation'] if (OUT/'continuation/run.json').exists() else [])
    regs=[json.loads((phase/'registration.json').read_text()) for phase in phases]
    hashes={name:digest for reg in regs for name,digest in reg['source_hashes'].items()}
    for name,digest in hashes.items():
        path=(SNAP/name) if name.startswith(('src/','scripts/')) else ROOT/name
        if path==OUT/'README.md' and (OUT/'prewritten.md').exists():path=OUT/'prewritten.md'
        assert p.sha(path)==digest,name
    rows=[row for phase in phases for row in lines(phase/'records.jsonl')];http=[row for phase in phases for row in lines(phase/'http/records.jsonl')]
    pairs={}
    for h in http:
        assert h['complete'] and h['done']
        cap=512 if h['pass_name']=='pilot' else 768
        ids=h['output_token_ids'];assert 0<len(ids)<=cap
        assert h['usage']['completion_tokens']==len(ids)
        assert h['usage']['prompt_tokens']==len(h['prompt_token_ids'])
        assert not any(i in (248046,248044) for i in ids[:-1])
        assert (h['finish_reason']=='stop' and ids[-1] in (248046,248044)) or (h['finish_reason']=='length' and len(ids)==cap)
        if h['pass_name']=='pilot':
            key=(h['index'],h['arm'],h['round'],runner.ids_hash(h['prompt_token_ids']))
            assert key not in pairs; pairs[key]=h
    assert len(pairs)>=len(rows) if '--partial' in sys.argv else len(pairs)==len(rows)
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
        assert slab.qwen_tokenizer().decode(r['output_token_ids'],skip_special_tokens=False)==r['output']
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
    sys.path.insert(0,str(SNAP/'scripts'))
    import focus_check40k as k
    from transformers import AutoTokenizer
    tok=AutoTokenizer.from_pretrained('/home/bmarti44/models/qwen3.8-27b-fp8',local_files_only=True)
    k.OUT=ROOT/'results/quick-checks/check40k'
    tasks={t['id']:t for t in k.bank() if t['split']=='eval'}
    js=lines(OUT/'js-records.jsonl');assert len(js)==32
    for r in js:
        assert r['messages']==k.j.messages(tasks[r['task_id']],'text-only')
        assert r['score']==k.score(r['output'],tasks[r['task_id']],r['truncated'])
        ids=tok.apply_chat_template(r['messages'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False)
        match=[h for h in http if h['pass_name']=='check40k' and h['prompt_token_ids']==ids]
        assert len(match)==1 and match[0]['output_token_ids']==r['token_ids']
        assert tok.decode(r['token_ids'],skip_special_tokens=True)==r['output']
    assert checked==32 and len(http)==64
    life=json.loads((OUT/'lifecycle.json').read_text());assert life['gpu_held_seconds']<=2400
    assert not (OUT/'RUNNING.flag').exists()
    result=dict(replay_source_commit="184cb321",live_worktree_drift_detected=True,isolated_frozen_replay=True,passed=True,dev_exact_consumer_replays=checked,js_hidden_test_replays=len(js),http_token_eos_cap_checks=len(http),source_hashes_verified=len(hashes),gpu_seconds=life['gpu_held_seconds'])
    (OUT/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':main()
