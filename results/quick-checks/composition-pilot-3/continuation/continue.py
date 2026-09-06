"""Conditional exact-context continuation; preserve every existing DEV observation."""
import concurrent.futures as cf
import fcntl
import os
import urllib.request
from dataclasses import replace
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import time
OUT=Path(__file__).resolve().parent
PARENT=OUT.parent
spec=importlib.util.spec_from_file_location('pilot3',PARENT/'run.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
p,slab=r.p,r.slab
from stencil.focus.loop import authenticate
from stencil.focus.renderer import render

def lines(path):return [json.loads(s) for s in path.read_text().splitlines()] if path.exists() else []
def exact(lane):
    entries=authenticate(lane.messages)
    register=lane.session.register.apply(entries)
    content=p.compact([dict(role=m.role,**({'tool_results':m.tool_results} if m.tool_results and (not m.text or m.text==p.compact(m.tool_results)) else {'text':m.text,**({'tool_results':m.tool_results} if m.tool_results else {})})) for m in lane.messages])+'\n'+lane.session.request.text
    req=replace(lane.session.request,text=content,history_ids=lane.session.history_ids,max_tokens=None)
    return render(register,req)

class ExactDecoder(r.Decoder):
    def __call__(self,req):
        assert tuple(req.prompt_ids)==tuple(self.lane.exact_ids)
        return super().__call__(req)

def restore(episode,arm,saved):
    with tempfile.TemporaryDirectory() as d:
        lane=p.Lane(Path(d),episode,arm,'c4')
        for row in saved:
            detail=row['oracle_checker_results'][0]
            lane.prepare(detail['round']);lane.gate=detail['paired_gate'];lane.measurement=detail['measurements']
            expected=exact(lane)
            assert list(expected.prompt_ids)==row['rendered_token_ids']
            def decoder(req):
                assert list(req.prompt_ids)==row['rendered_token_ids']
                return p.tool_calls(r.DecodeResult(row['output'],tuple(row['output_token_ids']),row['eos'],row['truncated']))
            replay=r.one(lane,decoder)
            assert replay['oracle_checker_results'][0]['outcome']==detail['outcome']
            assert replay['oracle_checker_results'][0]['artifact_hashes']==detail['artifact_hashes']
        dest=OUT/'c4'/episode.episode_id/arm
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.move(str(lane.directory),dest)
        lane.directory=dest;lane.out=OUT;lane.executor.directory=dest/'workspace'
        lane.session.journal.path=dest/'journal.jsonl'
    return lane

def resume(client,deadline,tokenizer):
    saved=lines(PARENT/'records.jsonl')
    grouped={}
    for row in saved:
        d=row['oracle_checker_results'][0];grouped.setdefault((d['episode'],d['arm']),[]).append(row)
    for rs in grouped.values():rs.sort(key=lambda row:row['oracle_checker_results'][0]['round'])
    episodes=slab.bank('dev')
    wave=max((s['wave'] for s in lines(PARENT/'schedule.jsonl')),default=-1)+1
    stages=[]
    for arms in [('R','N','T'),('O',)]:
        if arms==('O',):
            allstages=lines(PARENT/'stages.jsonl')+stages
            aggregate=sum(s['tokens'] for s in allstages)/sum(s['wall_seconds'] for s in allstages)
            # Worst-case O token count, no borrowing a missing O measurement.
            needed=1.25*sum(len(e.turns) for e in episodes)*512/aggregate+1000
            if time.time()+needed>=deadline:
                p.append(OUT/'events.jsonl',dict(event='optional_O_budget_skip',required_seconds=needed,remaining_seconds=deadline-time.time(),trait_cleanup_reserve=1000))
                return
        for group in [p.ORDER[:4],p.ORDER[4:]]:
            for arm in arms:
                start=time.time()
                lanes=[restore(episodes[i],arm,grouped.get((episodes[i].episode_id,arm),[])) for i in group]
                before={l.episode.episode_id:len(l.rows) for l in lanes}
                blocked=set()
                for index in range(max(len(l.episode.turns) for l in lanes)):
                    active=[l for l in lanes if len(l.rows)==index and index<len(l.episode.turns) and l.episode.episode_id not in blocked]
                    if not active:continue
                    if time.time()>=deadline-1000:
                        p.append(OUT/'events.jsonl',dict(event='required_work_budget_stop',remaining_seconds=deadline-time.time(),reserve_for_registered_trait_screen=1000))
                        break
                    admitted=[]
                    for lane in active:
                        estimated=lane.prepare(index);actual=exact(lane);n=len(actual.prompt_ids)
                        if n>32768-512:
                            blocked.add(lane.episode.episode_id)
                            p.append(OUT/'events.jsonl',dict(event='exact_context_rejection',episode=lane.episode.episode_id,arm=arm,round=index,actual_tokens=n,limit=32768-512))
                            continue
                        lane.exact_ids=actual.prompt_ids;lane.bound=32768-512
                        lane.gate=dict(allowed=True,bounds={arm:32768-512},estimated_bound=estimated,actual_tokens=n,policy='exact CPU renderer preflight, asserted again by actual loop before HTTP')
                        admitted.append(lane)
                    if not admitted:continue
                    p.append(OUT/'schedule.jsonl',dict(wave=wave,arm=arm,round=index,episodes=[l.episode.episode_id for l in admitted],started=time.time()))
                    with cf.ThreadPoolExecutor(max_workers=4) as pool:
                        futures=[pool.submit(r.one,l,ExactDecoder(client,tokenizer,deadline,l,wave)) for l in admitted]
                        for f in futures:f.result()
                    print('wave',wave,arm,index,[l.episode.episode_id for l in admitted],flush=True);wave+=1
                new=[row for l in lanes for row in l.rows[before[l.episode.episode_id]:]]
                stage=dict(arm=arm,group=list(group),wall_seconds=time.time()-start,tokens=sum(row['oracle_checker_results'][0]['measurements']['total_tokens'] for row in new),complete=all(len(l.rows)==len(l.episode.turns) for l in lanes),new_calls=len(new),restored_calls=sum(before.values()))
                stages.append(stage);p.append(OUT/'stages.jsonl',stage)
                for lane in lanes:
                    ids=list(lane.session.history_ids)
                    p.write(lane.directory/'final-transcript.json',dict(ids=ids,sha256=r.ids_hash(ids)))
                    p.append(OUT/'episodes.jsonl',dict(episode=lane.episode.episode_id,arm=arm,scheduled_rounds=len(lane.episode.turns),rounds=len(lane.rows),complete=len(lane.rows)==len(lane.episode.turns),output_sha256=r.ids_hash([x for row in lane.rows for x in list(row['output_token_ids'])+([] if row['eos'] is None else [row['eos']])]),transcript_sha256=r.ids_hash(ids),transcript_path=str((lane.directory/'final-transcript.json').relative_to(PARENT))))
                if time.time()>=deadline-1000:return

def smoke():
    saved=lines(PARENT/'records.jsonl')
    grouped={}
    for row in saved:
        d=row['oracle_checker_results'][0];grouped.setdefault((d['episode'],d['arm']),[]).append(row)
    checked=0
    with tempfile.TemporaryDirectory() as d:
        for (episode,arm),rows in grouped.items():
            lane=p.Lane(Path(d),slab.generate_episode('dev',int(episode.rsplit('-',1)[1])),arm,'smoke')
            for row in sorted(rows,key=lambda row:row['oracle_checker_results'][0]['round']):
                dt=row['oracle_checker_results'][0];lane.prepare(dt['round']);lane.gate=dt['paired_gate'];lane.measurement={}
                assert list(exact(lane).prompt_ids)==row['rendered_token_ids']
                rr=r.one(lane,lambda req:p.tool_calls(r.DecodeResult(row['output'],tuple(row['output_token_ids']),row['eos'],row['truncated'])))
                assert rr['oracle_checker_results'][0]['outcome']==dt['outcome'];checked+=1
    p.write(OUT/'cpu-preflight.json',dict(passed=True,exact_renderer_and_checker_rows=checked,dev_only=True))
    print('PASS exact preflight',checked)

def launch():
    reg=json.loads((OUT/'registration.json').read_text())
    for path,digest in reg['source_hashes'].items():assert p.sha(r.ROOT/path)==digest,path
    assert not (OUT/'run.json').exists()
    lock=(r.ROOT/'.review.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    flags=list((r.ROOT/'results/quick-checks').glob('*/RUNNING.flag'));assert not flags,flags
    gpu=r.cmd(['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader'])
    assert gpu['returncode']==0 and not any('python' in s for s in gpu['output'].splitlines()),gpu
    start=time.time();deadline=start+9000-reg['prior_pilot3_seconds']
    flag=PARENT/'RUNNING.flag'
    with flag.open('x') as f:json.dump(dict(pid=os.getpid(),start=start,deadline=deadline,phase='continuation'),f)
    receipt=dict(start=start,deadline=deadline,status='starting',occupancy=gpu)
    p.write(OUT/'run.json',receipt)
    name=f'stencil-pilot3-continuation-{int(start)}'
    args=list(reg['command']);args[args.index('--name')+1]=name;created=False
    r.OUT=OUT;client=r.load_client();tok=r.Tokenizer.from_file(str(slab.TOKENIZER_PATH))
    try:
        receipt['launch']=r.cmd(args);p.write(OUT/'run.json',receipt)
        assert receipt['launch']['returncode']==0,receipt['launch'];created=True
        p.write(OUT/'container.json',dict(name=name,id=receipt['launch']['output'].strip()))
        while time.time()<deadline-1000:
            state=r.cmd(['docker','inspect','--format','{{.State.Status}}',name]);assert state['output'].strip()=='running',state
            try:
                with urllib.request.urlopen(client.URL+'/health',timeout=2) as response:
                    if response.status==200:break
            except Exception:time.sleep(3)
        else:raise TimeoutError('startup exhausted reserved budget')
        receipt.update(status='ready',load_seconds=time.time()-start);p.write(OUT/'run.json',receipt)
        if not r.determinism(client,deadline):receipt['status']='determinism_stop';return
        client.metrics('before.prom');resume(client,deadline,tok);client.metrics('after.prom');receipt['status']='finished'
    except BaseException as exc:
        receipt.update(status='error',error=repr(exc));raise
    finally:
        if created:
            receipt['stop']=r.cmd(['docker','stop','-t','20',name])
            (OUT/'server.log').write_text(r.cmd(['docker','logs','--timestamps',name])['output'])
            p.write(OUT/'container-inspect.json',json.loads(r.cmd(['docker','inspect',name])['output']))
            receipt['remove']=r.cmd(['docker','rm',name])
        receipt.update(end=time.time(),gpu_held_seconds=time.time()-start);p.write(OUT/'run.json',receipt)
        flag.unlink(missing_ok=True);fcntl.flock(lock,fcntl.LOCK_UN)

if __name__=='__main__':
    if '--cpu' in sys.argv:smoke()
    else:
        assert not (PARENT/'RUNNING.flag').exists()
        assert any(e['event']=='context_stop' for e in lines(PARENT/'events.jsonl'))
        launch()
