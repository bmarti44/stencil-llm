"""Conditional eight-call lexical style competence screen; no candidate search."""
import ast
import concurrent.futures as cf
from dataclasses import asdict,replace
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import urllib.request
OUT=Path(__file__).resolve().parent;PARENT=OUT.parent
spec=importlib.util.spec_from_file_location('pilot3',PARENT/'run.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
p,slab=r.p,r.slab
LABELS={'2':'ALPHA','3':'BETA','4':'GAMMA'}
SYSTEM=p.SYSTEM_PROMPT.replace('Style indentation denotes a block width; continuation alignment is free. ',
    "For style docstring_prefix=LABEL, every emitted function's first statement must be a docstring whose text starts with LABEL followed by a colon. Ordinary Python indentation is free. ")
BASE={}
def digest(obj):return hashlib.sha256(p.compact(obj).encode()).hexdigest()
def transform(e):
    turns=[]
    for t in e.turns:
        events=[]
        for entry in t.events:
            if entry.kind=='style':
                label=LABELS[entry.value]
                entry=replace(entry,key='docstring_prefix',value=label,event_id=entry.event_id.replace(':indent:',':docstring_prefix:'),
                    text=f'Workshop obligation: docstring_prefix must be {label}. Every emitted function begins with a docstring starting {label}:')
            events.append(entry)
        def values(items):return tuple(sorted(('docstring_prefix',LABELS[v]) if k=='indent' else (k,v) for k,v in items))
        live,retired=values(t.live),values(t.retired)
        changes=' '.join(f'{v.action} {v.key} -> {v.value}.'+ (f' Every emitted function begins with a docstring starting {v.value}:' if v.kind=='style' else '') for v in events)
        text=t.t_text
        for number,label in LABELS.items():
            text=text.replace(f'indent={number} indent {number} = block bodies indented by exactly {number} spaces.',f'docstring_prefix={label}')
            text=text.replace(f'indent={number}',f'docstring_prefix={label}')
        turns.append(replace(t,events=tuple(events),live=live,retired=retired,request=changes+'\n'+t.request.split('\n',1)[1],t_text=text))
    return replace(e,turns=tuple(turns))

def markers(code):
    try:
        nodes=[n for n in ast.walk(ast.parse(code)) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
        return [ast.get_docstring(n,clean=False) for n in nodes]
    except (SyntaxError,ValueError):return []

def checker(episode,turn,output,executor,executed=True,truncated=False):
    result=slab.check(BASE[episode.episode_id],turn,output,executor,executed=executed,truncated=truncated)
    label=dict(episode.turns[turn].live)['docstring_prefix']
    codes=executor.emitted_codes
    eligible=[markers(code) for code in codes if markers(code)]
    compliant=sum(all(isinstance(s,str) and s.startswith(label+':') for s in group) for group in eligible)
    okay=bool(eligible and compliant==len(eligible))
    result['violations']['style']=not okay
    result['prior_trait_present']['style']=False
    result['prior_compliance']['style']=False
    result['relapse']['style']=False;result['attempted_relapse']['style']=False
    result['style_carrier']=dict(label=label,eligible_executed_edits=len(eligible),compliant_edits=compliant if not truncated else 0,
        compliant_response=okay and bool(executor.executed) and not truncated,observed_docstrings=[s for group in eligible for s in group])
    result['success']=not any(result['violations'].values())
    return result

def install():
    if not BASE:BASE.update({e.episode_id:e for e in slab.bank('dev')})
    p.SYSTEM_PROMPT=SYSTEM;p.check=checker

def witness(e,variant):
    obj=json.loads(slab.reference(BASE[e.episode_id],0));label=dict(e.turns[0].live)['docstring_prefix']
    for call in obj['calls']:
        if call['op'] not in ('edit','replace'):continue
        tree=ast.parse(call['code'])
        for node in ast.walk(tree):
            if not isinstance(node,ast.FunctionDef):continue
            assert ast.get_docstring(node,clean=False) is not None
            if variant=='missing':node.body.pop(0)
            else:node.body[0].value.value=(label if variant!='wrong' else {'ALPHA':'BETA','BETA':'GAMMA','GAMMA':'ALPHA'}[label])+': '+node.body[0].value.value
        call['code']=ast.unparse(tree)
    return p.compact(obj)

def cpu():
    assert json.loads((OUT/'activation.json').read_text())['original_indent_gate_failed']
    assert not (PARENT/'RUNNING.flag').exists(), 'CPU activation follows original GPU run'
    install();episodes=[transform(BASE[f'slab-dev-{i:02}']) for i in p.ORDER]
    manifest=dict(system=SYSTEM,system_sha256=hashlib.sha256(SYSTEM.encode()).hexdigest(),mapping=LABELS,
        episodes=[dict(episode=asdict(e),sha256=digest(asdict(e))) for e in episodes],scope='DEV only; round-zero competence only')
    p.write(OUT/'frozen.json',manifest)
    checks=[]
    with tempfile.TemporaryDirectory() as d:
        for e in episodes:
            for variant in ('positive','wrong','missing','capped'):
                lane=p.Lane(Path(d),e,'R',variant);lane.prepare(0);lane.gate=dict(allowed=True,bounds={'R':lane.bound});lane.measurement=dict(cpu_stub=True)
                text=witness(e,variant);ids=slab.qwen_encode(text)
                assert len(ids)<512
                if variant=='capped':
                    assert slab.qwen_tokenizer().decode([220])==' '
                    ids=tuple(ids)+(220,)*(512-len(ids));text=slab.qwen_tokenizer().decode(list(ids),skip_special_tokens=False)
                def decode(req):
                    assert len(req.prompt_ids)<=lane.bound<=32256
                    return p.tool_calls(r.DecodeResult(text,ids,None if variant=='capped' else 151645,variant=='capped'))
                row=r.one(lane,decode)
                outcome=row['oracle_checker_results'][0]['outcome'];got=outcome['style_carrier']['compliant_response']
                assert got==(variant=='positive'),(e.episode_id,variant,outcome)
                assert not outcome['violations']['semantic']
                checks.append(dict(episode=e.episode_id,variant=variant,compliant=got))
    p.write(OUT/'cpu-witnesses.json',dict(passed=True,checks=checks,exact_v2_writer=True,dev_only=True))
    print('PASS',len(checks),'style witnesses through the actual loop/executor/checker')

def screen(client,deadline,tok):
    install();episodes=[transform(BASE[f'slab-dev-{i:02}']) for i in p.ORDER]
    frozen=json.loads((OUT/'frozen.json').read_text())
    assert [digest(asdict(e)) for e in episodes]==[e['sha256'] for e in frozen['episodes']]
    started=time.time()
    for wave in range(2):
        if time.time()>deadline-240:raise TimeoutError('style call reserve')
        lanes=[p.Lane(OUT,e,'R','c4') for e in episodes[4*wave:4*wave+4]]
        for lane in lanes:lane.prepare(0);lane.gate=dict(allowed=lane.bound<=32256,bounds={'R':lane.bound})
        assert all(l.gate['allowed'] for l in lanes)
        p.append(OUT/'schedule.jsonl',dict(wave=wave,episodes=[l.episode.episode_id for l in lanes],arm='R',round=0,started=time.time()))
        with cf.ThreadPoolExecutor(max_workers=4) as pool:
            fs=[pool.submit(r.one,l,r.Decoder(client,tok,deadline,l,wave)) for l in lanes]
            for f in fs:f.result()
        for lane in lanes:
            ids=list(lane.session.history_ids);p.write(lane.directory/'final-transcript.json',dict(ids=ids,sha256=r.ids_hash(ids)))
            row=lane.rows[0]
            full=list(row['rendered_token_ids'])+list(row['output_token_ids'])+([] if row['eos'] is None else [row['eos']])
            hf=lane.directory/'hf-final-input.json';p.write(hf,dict(ids=full,sha256=r.ids_hash(full),contains_system=True))
            p.append(OUT/'transcripts.jsonl',dict(episode=lane.episode.episode_id,arm='R',retained_history_sha256=r.ids_hash(ids),hf_final_transcript_sha256=r.ids_hash(full),hf_final_transcript_path=str(hf.relative_to(PARENT)),
                transcript_path=str((lane.directory/'final-transcript.json').relative_to(PARENT)),measurements=row['oracle_checker_results'][0]['measurements']))
    p.write(OUT/'screen-timing.json',dict(wall_seconds=time.time()-started))

def launch():
    reg=json.loads((OUT/'registration.json').read_text())
    for path,h in reg['source_hashes'].items():assert p.sha(r.ROOT/path)==h,path
    assert not (OUT/'run.json').exists()
    lock=(r.ROOT/'.review.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    flags=list((r.ROOT/'results/quick-checks').glob('*/RUNNING.flag'));assert not flags,flags
    gpu=r.cmd(['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader'])
    assert gpu['returncode']==0 and not any('python' in s for s in gpu['output'].splitlines()),gpu
    start=time.time();deadline=start+9000-reg['prior_pilot3_seconds'];flag=PARENT/'RUNNING.flag'
    with flag.open('x') as f:json.dump(dict(pid=os.getpid(),start=start,deadline=deadline,phase='trait-swap'),f)
    receipt=dict(start=start,deadline=deadline,status='starting',occupancy=gpu);p.write(OUT/'run.json',receipt)
    name=f'stencil-pilot3-trait-{int(start)}';args=list(reg['command']);args[args.index('--name')+1]=name;created=False
    r.OUT=OUT;client=r.load_client();tok=r.Tokenizer.from_file(str(slab.TOKENIZER_PATH))
    try:
        receipt['launch']=r.cmd(args);p.write(OUT/'run.json',receipt);assert receipt['launch']['returncode']==0;created=True
        p.write(OUT/'container.json',dict(name=name,id=receipt['launch']['output'].strip()))
        while time.time()<deadline-240:
            status=r.cmd(['docker','inspect','--format','{{.State.Status}}',name]);assert status['output'].strip()=='running',status
            try:
                with urllib.request.urlopen(client.URL+'/health',timeout=2) as response:
                    if response.status==200:break
            except Exception:time.sleep(3)
        else:raise TimeoutError('style startup budget')
        receipt.update(status='ready',load_seconds=time.time()-start);p.write(OUT/'run.json',receipt)
        # Same fixed eight-prompt schedule-level gate on this fresh server.
        if not r.determinism(client,deadline):receipt['status']='determinism_stop';return
        client.metrics('before.prom');screen(client,deadline,tok);client.metrics('after.prom');receipt['status']='finished'
    except BaseException as exc:receipt.update(status='error',error=repr(exc));raise
    finally:
        if created:
            receipt['stop']=r.cmd(['docker','stop','-t','20',name]);(OUT/'server.log').write_text(r.cmd(['docker','logs','--timestamps',name])['output'])
            p.write(OUT/'container-inspect.json',json.loads(r.cmd(['docker','inspect',name])['output']));receipt['remove']=r.cmd(['docker','rm',name])
        receipt.update(end=time.time(),gpu_held_seconds=time.time()-start);p.write(OUT/'run.json',receipt)
        flag.unlink(missing_ok=True);fcntl.flock(lock,fcntl.LOCK_UN)
def audit():
    install()
    reg=json.loads((OUT/'registration.json').read_text())
    for path,h in reg['source_hashes'].items():assert p.sha(r.ROOT/path)==h,path
    rows=[json.loads(x) for x in (OUT/'records.jsonl').read_text().splitlines()]
    assert len(rows)==8
    http=[json.loads(x) for x in (OUT/'http/records.jsonl').read_text().splitlines()]
    assert len(http)==32 and all(h['complete'] for h in http)
    results=[]
    with tempfile.TemporaryDirectory() as d:
        for row in rows:
            dt=row['oracle_checker_results'][0];e=transform(BASE[dt['episode']]);lane=p.Lane(Path(d),e,'R','audit');lane.prepare(0)
            lane.gate=dt['paired_gate'];lane.measurement={}
            def decode(req):
                assert list(req.prompt_ids)==row['rendered_token_ids']
                return p.tool_calls(r.DecodeResult(row['output'],tuple(row['output_token_ids']),row['eos'],row['truncated']))
            fresh=r.one(lane,decode)['oracle_checker_results'][0]
            assert fresh['outcome']==dt['outcome']
            for key in ('executed','results','tolerances'):assert json.loads(json.dumps(fresh['execution'][key]))==dt['execution'][key]
            assert fresh['artifact_hashes']==dt['artifact_hashes']
            output=row['output_token_ids']+([] if row['eos'] is None else [row['eos']])
            match=next(h for h in http if h['pass_name']=='pilot' and h['prompt_token_ids']==row['rendered_token_ids'])
            assert match['output_token_ids']==output
            hf=json.loads((OUT/'c4'/dt['episode']/'R/hf-final-input.json').read_text())
            assert hf['ids']==row['rendered_token_ids']+output and hf['sha256']==r.ids_hash(hf['ids'])
            results.append(dict(episode=dt['episode'],**dt['outcome']['style_carrier'],truncated=row['truncated'],executed_tools=len(dt['execution']['executed']),tokens=len(output),seconds=row['wall_seconds']))
    gate=json.loads((OUT/'determinism.json').read_text());assert gate['passed'] and gate['D']==0
    cold={h['index']:h['output_token_ids'] for h in http if h['pass_name']=='b1_cold'}
    for h in http:
        if h['pass_name'] in ('b1_warm','b4_mixed'):assert h['output_token_ids']==cold[h['index']]
    run=json.loads((OUT/'run.json').read_text())
    assert run['stop']['returncode']==run['remove']['returncode']==0
    assert run['gpu_held_seconds']+reg['prior_pilot3_seconds']<=9000
    inspection=json.loads((OUT/'container-inspect.json').read_text())[0]
    assert inspection['Image']=='sha256:ffa30d66ff5c9346c6389507cc529827fc9934a6d2ee37855934f94fe1061cdc' and not inspection['State']['Running']
    good=sum(x['compliant_response'] for x in results);eligible=sum(x['eligible_executed_edits'] for x in results);edits=sum(x['compliant_edits'] for x in results)
    wall=json.loads((OUT/'screen-timing.json').read_text())['wall_seconds']
    summary=dict(reading='COMPETENCE PASS' if good>=4 and eligible and edits/eligible>=.5 else 'COMPETENCE FAIL',responses=good,required_responses=8,compliant_edits=edits,eligible_executed_edits=eligible,episodes=results,
        aggregate_tok_s=sum(x['tokens'] for x in results)/wall,screen_wall_seconds=wall,gpu_held_seconds=run['gpu_held_seconds'],all_pilot3_gpu_seconds=run['gpu_held_seconds']+reg['prior_pilot3_seconds'],determinism=gate,
        claim='round-zero lexical competence only; no larger eligibility or post-retirement claim')
    p.write(OUT/'summary.json',summary);p.write(OUT/'audit.json',dict(passed=True,exact_CPU_replays=8,HTTP_calls=32,full_HF_input_hashes_verified=8,cleanup=True,total_budget=True))
    print(json.dumps(summary,indent=2))

if __name__=='__main__':
    if '--cpu' in sys.argv:cpu()
    elif '--audit' in sys.argv:audit()
    else:launch()
