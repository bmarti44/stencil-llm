"""Bounded DEV-only pilot, qualified serving with in-process package loop."""
import concurrent.futures as cf
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT = Path('/home/bmarti44/stencil-llm')
sys.path.insert(0, str(ROOT))
from scripts import composition_pilot as p
from stencil.focus.loop import DecodeResult, generate_once
from stencil.focus.journal import FIELDS
from stencil.focus import slab
from tokenizers import Tokenizer
OUT = Path(__file__).resolve().parent
QUAL = ROOT / 'results/quick-checks/vllm-qual'

def guard(event, args):
    if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)):
        path = os.fsdecode(args[0])
        if '/data/bench' in str(Path(path).absolute()):
            raise RuntimeError('forbidden benchmark access')

sys.addaudithook(guard)
_original_generate = slab.generate_episode
def dev_only(family='dev', index=0, seed=20260906):
    assert family == 'dev', 'DEV only'
    return _original_generate(family, index, seed)
slab.generate_episode = dev_only

def load_client():
    spec = importlib.util.spec_from_file_location('qualified_replay', QUAL / 'replay.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.OUT = OUT / 'http'
    module.OUT.mkdir(exist_ok=True)
    return module

def cmd(args):
    r = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return dict(args=args, returncode=r.returncode, output=r.stdout)

def ids_hash(ids):
    return hashlib.sha256(p.compact(list(ids)).encode()).hexdigest()

class Decoder:
    def __init__(self, client, tokenizer, deadline, lane, wave):
        self.client, self.tokenizer, self.deadline = client, tokenizer, deadline
        self.lane, self.wave = lane, wave
    def __call__(self, req):
        lane = self.lane
        assert len(req.prompt_ids) <= lane.bound <= 32768-512
        row = self.client.call('pilot', self.wave, dict(arm=lane.arm, round=lane.round,
            prompt=list(req.prompt_ids)), self.deadline)
        assert row['complete'], row.get('error')
        ids = row['output_token_ids']
        eos = ids[-1] if row['finish_reason'] == 'stop' else None
        body = ids[:-1] if eos is not None else ids
        lane.measurement = dict(backend='vllm-qualified', backend_identity='registration.json',
            wave=self.wave, http_index=self.wave, episode=lane.episode.episode_id,
            started=row['started'], wall_seconds=row['wall_seconds'],
            ttft_seconds=row['ttft_seconds'], decode_seconds=row['decode_seconds'],
            decode_tokens=row['decode_tokens'], total_tokens=len(ids),
            hidden_state_capture=False, prompt_sha256=ids_hash(req.prompt_ids),
            output_sha256=ids_hash(ids), transcript_sha256=ids_hash(list(req.prompt_ids)+ids))
        return p.tool_calls(DecodeResult(self.tokenizer.decode(body, skip_special_tokens=False),
            tuple(body), eos, eos is None, gpu_held_seconds=row['wall_seconds']))

def one(lane, decoder):
    generate_once(lane.session, lane.messages, decoder, tools=p.TOOL_SCHEMA)
    row = lane.rows[-1]
    assert set(row) == FIELDS
    assert 'tolerances' in row['oracle_checker_results'][0]['execution']
    assert not row['oracle_checker_results'][0]['hidden']
    assert not row['failures']
    return row

def smoke():
    episodes = slab.bank('dev')
    with tempfile.TemporaryDirectory() as d:
        lanes = [p.Lane(Path(d), episodes[i], 'R', 'smoke') for i in p.ORDER[:4]]
        for index in range(32):
            active = [l for l in lanes if index < len(l.episode.turns)]
            for lane in active:
                lane.prepare(index); lane.gate = dict(allowed=True, bounds={lane.arm:lane.bound})
            def work(lane):
                text = slab.reference(lane.episode, index)
                lane.measurement = dict(cpu_stub=True)
                row = one(lane, lambda req: p.tool_calls(DecodeResult(text,
                    slab.qwen_encode(text),151645,False)))
                assert row['oracle_checker_results'][0]['outcome']['success']
            with cf.ThreadPoolExecutor(max_workers=4) as pool:
                list(pool.map(work, active))
        assert sum(len(l.rows) for l in lanes)==96
    p.write(OUT/'smoke.json', dict(passed=True, records=96, lengths=[16,16,32,32],
        fields=sorted(FIELDS), cpu_only=True, dev_only=True))

def determinism(client, deadline):
    frozen = json.loads((QUAL/'frozen.json').read_text())[:8]
    assert {f['arm'] for f in frozen} == set('RNTO')
    passes = []
    for name, workers in [('b1_cold',1),('b1_warm',1),('b4_mixed',4)]:
        rows=[]
        for offset in range(0,8,workers):
            with cf.ThreadPoolExecutor(max_workers=workers) as pool:
                rows.extend(pool.map(lambda i: client.call(name,i,frozen[i],deadline),
                    range(offset, min(offset+workers,8))))
        passes.append(rows)
    differences=[]
    for i in range(8):
        a=passes[0][i]
        for j in (1,2):
            b=passes[j][i]
            if not a['complete'] or not b['complete'] or a['output_token_ids']!=b['output_token_ids']:
                differences.append(dict(index=i, pass_name=b['pass_name']))
    result=dict(passed=not differences, differences=differences, D=len(differences),
        calls=24, frozen_indices=list(range(8)), frozen_sha256=p.sha(QUAL/'frozen.json'))
    p.write(OUT/'determinism.json',result)
    return result['passed']

def trajectories(client, deadline, tokenizer):
    episodes=slab.bank('dev'); wave=0; stages=[]
    for arms in [('R','N','T'),('O',)]:
        if arms==('O',):
            rate=sum(s['tokens'] for s in stages)/sum(s['wall_seconds'] for s in stages)
            r_tokens=sum(s['tokens'] for s in stages if s['arm']=='R')
            estimate=1.5*r_tokens/rate+180
            if time.time()+estimate>=deadline:
                p.append(OUT/'events.jsonl',dict(event='optional_O_budget_skip',estimate=estimate))
                return
        for group in [p.ORDER[:4],p.ORDER[4:]]:
            for arm in arms:
                lanes=[p.Lane(OUT,episodes[i],arm,'c4') for i in group]
                start=time.time(); complete=True
                for index in range(max(len(l.episode.turns) for l in lanes)):
                    if time.time()>=deadline-240:
                        complete=False; break
                    active=[l for l in lanes if index<len(l.episode.turns)]
                    for lane in active:
                        lane.prepare(index)
                        lane.gate=dict(allowed=lane.bound<=32768-512,
                            bounds={arm:lane.bound},policy='same conservative per-lane bound all arms')
                    if any(not l.gate['allowed'] for l in active):
                        p.append(OUT/'events.jsonl',dict(event='context_stop',arm=arm,round=index,
                            episodes=[l.episode.episode_id for l in active],bounds=[l.bound for l in active]))
                        complete=False; break
                    p.append(OUT/'schedule.jsonl',dict(wave=wave,arm=arm,round=index,
                        episodes=[l.episode.episode_id for l in active],started=time.time()))
                    with cf.ThreadPoolExecutor(max_workers=4) as pool:
                        futures=[pool.submit(one,l,Decoder(client,tokenizer,deadline,l,wave)) for l in active]
                        for future in futures: future.result()
                    print('wave',wave,arm,index,[l.episode.episode_id for l in active],flush=True)
                    wave+=1
                wall=time.time()-start
                stage=dict(arm=arm,group=list(group),wall_seconds=wall,
                    tokens=sum(r['oracle_checker_results'][0]['measurements']['total_tokens'] for l in lanes for r in l.rows),
                    complete=complete)
                stages.append(stage);p.append(OUT/'stages.jsonl',stage)
                for lane in lanes:
                    transcript=list(lane.session.history_ids)
                    p.write(lane.directory/'final-transcript.json',dict(ids=transcript,sha256=ids_hash(transcript)))
                    p.append(OUT/'episodes.jsonl',dict(episode=lane.episode.episode_id,arm=arm,
                        scheduled_rounds=len(lane.episode.turns),rounds=len(lane.rows),
                        complete=len(lane.rows)==len(lane.episode.turns),
                        output_sha256=ids_hash([x for r in lane.rows for x in r['output_token_ids']+([] if r['eos'] is None else [r['eos']])]),
                        transcript_sha256=ids_hash(transcript),
                        transcript_path=str((lane.directory/'final-transcript.json').relative_to(OUT))))
                if not complete:return

def main():
    if '--smoke' in sys.argv: return smoke()
    assert not (OUT/'run.json').exists(), 'fresh output required'
    reg=json.loads((OUT/'registration.json').read_text())
    for path,digest in reg['source_hashes'].items(): assert p.sha(ROOT/path)==digest,path
    client=load_client()
    tok=Tokenizer.from_file(str(slab.TOKENIZER_PATH))
    lock=(ROOT/'.review.lock').open('a')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    while True:
        flags=list((ROOT/'results/quick-checks').glob('*/RUNNING.flag'))
        gpu=cmd(['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader'])
        assert gpu['returncode']==0,gpu
        if not flags and not any('python' in s for s in gpu['output'].splitlines()):break
        print('waiting for Stencil GPU occupancy',flags,gpu,flush=True);time.sleep(30)
    start=time.time();deadline=start+9000
    flag=OUT/'RUNNING.flag'
    with flag.open('x') as f:json.dump(dict(pid=os.getpid(),start=start,deadline=deadline),f)
    receipt=dict(start=start,deadline=deadline,status='starting',occupancy=gpu)
    p.write(OUT/'run.json',receipt)
    name=f'stencil-composition-pilot-3-{int(start)}'
    args=json.loads((QUAL/'attempts.json').read_text())[0]['command']
    args[args.index('--name')+1]=name
    created=False
    try:
        launch=cmd(args);receipt['launch']=launch;p.write(OUT/'run.json',receipt)
        assert launch['returncode']==0,launch
        created=True
        p.write(OUT/'container.json',dict(name=name,id=launch['output'].strip()))
        while time.time()<deadline-300:
            status=cmd(['docker','inspect','--format','{{.State.Status}}',name])
            assert status['output'].strip()=='running',status
            try:
                with urllib.request.urlopen(client.URL+'/health',timeout=2) as r:
                    if r.status==200:break
            except Exception:time.sleep(3)
        else:raise TimeoutError('startup deadline')
        receipt['load_seconds']=time.time()-start;receipt['status']='ready';p.write(OUT/'run.json',receipt)
        (OUT/'server.log').write_text(cmd(['docker','logs','--timestamps',name])['output'])
        if not determinism(client,deadline):receipt['status']='determinism_stop';return
        client.metrics('before.prom')
        trajectories(client,deadline,tok)
        client.metrics('after.prom')
        receipt['status']='finished'
    except BaseException as exc:
        receipt.update(status='error',error=repr(exc));raise
    finally:
        if created:
            receipt['stop']=cmd(['docker','stop','-t','20',name])
            (OUT/'server.log').write_text(cmd(['docker','logs','--timestamps',name])['output'])
            inspection=cmd(['docker','inspect',name]);p.write(OUT/'container-inspect.json',json.loads(inspection['output']))
            receipt['remove']=cmd(['docker','rm',name])
        receipt.update(end=time.time(),gpu_held_seconds=time.time()-start)
        p.write(OUT/'run.json',receipt)
        flag.unlink(missing_ok=True)
        fcntl.flock(lock,fcntl.LOCK_UN)
if __name__=='__main__':main()
