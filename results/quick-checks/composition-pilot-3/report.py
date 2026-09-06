"""CPU report; exact per-call records are authoritative, never infer missing runs."""
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path('/home/bmarti44/stencil-llm');sys.path.insert(0,str(ROOT))
from scripts import composition_pilot as p
from stencil.focus import slab
OUT=Path(__file__).resolve().parent
KINDS=('language','style','format','process')
def lines(path):return [json.loads(s) for s in path.read_text().splitlines()] if path.exists() else []
def detail(r):return r['oracle_checker_results'][0]
def rate(a,b):return a/b if b else None

def stats(rows):
    ds=[detail(r) for r in rows]
    relapse={}
    for kind in KINDS:
        eligible=[d for d in ds if d['outcome']['denominators'][kind] and d['outcome']['prior_trait_present'][kind]]
        relapse[kind]=dict(numerator=sum(d['outcome']['relapse'][kind] for d in eligible),denominator=len(eligible),
            opportunity_episodes=sorted({d['episode'] for d in eligible}),
            relapsing_episodes=sorted({d['episode'] for d in eligible if d['outcome']['relapse'][kind]}))
    compliance=dict(required=0,parsed_edit_attempts=0,executed_edits=0,compliant=0,details=[])
    for r in rows:
        d=detail(r)
        if d['round']!=0:continue
        compliance['required']+=1
        widths=[];attempts=[]
        try:
            calls=slab.parse_envelope(r['output'])['calls']
            attempts=[c for c in calls if c.get('op') in ('edit','replace')]
            widths=[v for c in attempts for v in slab.indent_widths(c['code'])]
        except (ValueError,KeyError,TypeError):pass
        executed=[c for c in d['execution']['executed'] if c.get('op') in ('edit','replace')]
        ok=bool(executed and widths and not d['outcome']['violations']['style'] and not r['truncated'])
        compliance['parsed_edit_attempts']+=len(attempts);compliance['executed_edits']+=len(executed)
        compliance['compliant']+=ok
        compliance['details'].append(dict(episode=d['episode'],widths=widths,compliant=ok))
    violations={k:sum(d['outcome']['violations'][k] for d in ds) for k in (*KINDS,'wrong_family','breakage','semantic')}
    cumulative=[]
    for r in rows:
        d=detail(r)
        # Diagnostic attempted JSON extraction only; never feeds parser/executor.
        names=[]
        try:
            for c in json.loads(r['output']).get('calls',[]):
                if c.get('op') in ('edit','replace'):
                    names.extend(n.name for n in ast.parse(c['code']).body if isinstance(n,ast.FunctionDef))
        except (ValueError,SyntaxError,KeyError,TypeError):pass
        if len(names)>1:cumulative.append(dict(episode=d['episode'],round=d['round'],names=names,op='attempted edits/replaces'))
    return dict(calls=len(rows),executed_responses=sum(bool(d['execution']['executed']) for d in ds),
        executed_tools=sum(len(d['execution']['executed']) for d in ds),
        truncated=sum(bool(r['truncated']) for r in rows),
        stale_execution_rounds=sum(bool(d['execution']['executed']) and any(d['outcome']['relapse'].values()) for d in ds),
        wrong_skill_rounds=violations['wrong_family'],violations=violations,relapse=relapse,
        round0_indent=compliance,output_tokens=sum(d['measurements']['total_tokens'] for d in ds),
        seconds_per_call=rate(sum(r['wall_seconds'] for r in rows),len(rows)),
        request_seconds=sum(r['wall_seconds'] for r in rows),
        decode_tok_s=rate(sum(d['measurements']['decode_tokens'] for d in ds),sum(d['measurements']['decode_seconds'] or 0 for d in ds)),
        max_context=max((r['input_token_count'] for r in rows),default=None),
        tolerances=dict(Counter(t['tolerance'] for d in ds for t in d['execution']['tolerances'])),
        multi_function_reemissions=cumulative,
        in_100_300=sum(100<=r['output_token_count']<=300 for r in rows))

def main():
    rows=lines(OUT/'records.jsonl');episodes=lines(OUT/'episodes.jsonl');stages=lines(OUT/'stages.jsonl')
    run=json.loads((OUT/'run.json').read_text());gate=json.loads((OUT/'determinism.json').read_text())
    per_arm={a:stats([r for r in rows if detail(r)['arm']==a]) for a in 'RNTO'}
    endpoints=[]
    for ep in episodes:
        selected=sorted([r for r in rows if (detail(r)['episode'],detail(r)['arm'])==(ep['episode'],ep['arm'])],key=lambda r:detail(r)['round'])
        endpoints.append(dict(ep,metrics=stats(selected),final_success=detail(selected[-1])['outcome']['success'] if ep['complete'] else None,
            final_integration=detail(selected[-1])['outcome']['integration'] if ep['complete'] else None))
    total_tokens=sum(s['tokens'] for s in stages);wall=sum(s['wall_seconds'] for s in stages)
    aggregate=rate(total_tokens,wall)
    perarm_tokens={a:max((e['metrics']['output_tokens'] for e in endpoints if e['arm']==a and e['complete']),default=None) for a in 'RNTO'}
    prior_paths=['composition-pilot/run.json','composition-pilot-2/run.json','vllm-qual/lifecycle.json']
    prior={s:json.loads((OUT.parent/s).read_text())['gpu_held_seconds'] for s in prior_paths}
    # Failed first startup was separate from qualification's successful lifecycle.
    initial=json.loads((OUT.parent/'vllm-qual/initial-lifecycle.json').read_text())
    prior['vllm-qual/initial-lifecycle.json']=initial['gpu_held_seconds']
    weighted=64*(perarm_tokens['R']+perarm_tokens['N'])+16*(perarm_tokens['T']+perarm_tokens['O']) if all(v is not None for v in perarm_tokens.values()) else None
    projected=(sum(prior.values())+run['gpu_held_seconds']+run['load_seconds']+1.25*weighted/aggregate)/3600 if weighted and aggregate else None
    failures=[]
    if not gate['passed']:failures.append('D !=0 or incomplete determinism')
    if sum(e['complete'] and e['arm'] in 'RNT' for e in endpoints)!=24:failures.append('incomplete required R/N/T DEV trajectories')
    r=per_arm['R'];c=r['round0_indent']
    if c['required']!=8 or c['compliant']<4:failures.append('R round0 indentation <50% or incomplete')
    for a in 'RNT':
        s=per_arm[a]
        if not s['calls'] or s['executed_responses']/s['calls']<.9:failures.append(a+' executed-call rate <90%')
        if not s['calls'] or s['truncated']/s['calls']>.02:failures.append(a+' truncation >2%')
    r_success=sum(e['final_success'] is True for e in endpoints if e['arm']=='R')
    if r_success<5:failures.append('R final success <5/8')
    eligible_kinds=[k for k,v in r['relapse'].items() if len(v['opportunity_episodes'])>=2]
    if len(eligible_kinds)<2:failures.append('R executed-trait opportunities in >=2 episodes for <2 kinds')
    if not rows or max(r['input_token_count'] for r in rows)>32768-512:failures.append('context missing or exceeds32256')
    if projected is None or projected>12:failures.append('served cost projection unmeasured or >12h')
    failures.append('check45 HF teacher-forced recovery cost unmeasured (prewritten full-cost condition)')
    trigger=[]
    for k,v in r['relapse'].items():
        if v['denominator']>=20 and v['numerator']/v['denominator']>=.15 and len(v['relapsing_episodes'])>=2 and len(per_arm['O']['relapse'][k]['relapsing_episodes'])>=2:trigger.append(k)
    manifest=dict(hidden_states_captured=False,required='Check45 HF teacher-forced prefill; layers8/16/24/32/40; last-prompt and mean over all body positions, EOS excluded; forward last body token even at cap. HF-conditioned activations, not vLLM hidden states.',
        hash_encoding='SHA256 of compact JSON integer list',
        episodes=[{k:e[k] for k in ('episode','arm','complete','output_sha256','transcript_sha256','transcript_path')} for e in episodes],
        calls=[dict(episode=detail(r)['episode'],arm=detail(r)['arm'],round=detail(r)['round'],
            prompt_sha256=detail(r)['measurements']['prompt_sha256'],output_sha256=detail(r)['measurements']['output_sha256'],
            transcript_sha256=detail(r)['measurements']['transcript_sha256'],body_tokens=len(r['output_token_ids']),eos=r['eos'],truncated=r['truncated']) for r in rows])
    p.write(OUT/'transcript-manifest.json',manifest)
    summary=dict(reading='INELIGIBLE' if failures else 'ELIGIBLE',failures=failures,per_arm=per_arm,endpoints=endpoints,
        R_final_success=r_success,R_opportunity_kinds=eligible_kinds,run=run,determinism=gate,
        cost=dict(aggregate_tok_s=aggregate,stage_wall_seconds=wall,tokens=total_tokens,prior_seconds=prior,
            max_episode_tokens=perarm_tokens,weighted_future_tokens=weighted,served_projection_hours=projected,
            HF_recovery_seconds=None,full_projection_hours=None,charged_pilot_hours=run['gpu_held_seconds']/3600),
        DEV_mask_trigger=dict(met=bool(trigger),kinds=trigger,requires_state_audit=True),
        output_band='100-300 diagnostic, unchanged',backend='qualified vLLM; package path outcome-unvalidated')
    p.write(OUT/'summary.json',summary)
    # Keep preregistration byte-for-byte as its own artifact, before updating README.
    prereg=OUT/'prewritten.md'
    if not prereg.exists():prereg.write_bytes((OUT/'README.md').read_bytes())
    body='# Composition pilot 3 — '+summary['reading']+'\n\n'
    body+=f"Completed {len(rows)} calls; R final success **{r_success}/8**. "
    body+=f"Round-0 R indent **{c['compliant']}/{c['required']}**. Determinism **D={gate['D']}**, 24 calls.\n\n"
    body+='Failed/unmeasured gates: '+ '; '.join(failures)+'.\n\n'
    body+='| Arm | Calls executed | Caps | Final success | Stale execution | Wrong skill | Breakage | Decode tok/s | s/call |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|\n'
    for a,s in per_arm.items():
        finals=sum(e['final_success'] is True for e in endpoints if e['arm']==a);n=sum(e['complete'] for e in endpoints if e['arm']==a)
        body+=f"|{a}|{s['executed_responses']}/{s['calls']}|{s['truncated']}|{finals}/{n}|{s['stale_execution_rounds']}|{s['wrong_skill_rounds']}|{s['violations']['breakage']}|{s['decode_tok_s'] or 0:.3f}|{s['seconds_per_call'] or 0:.3f}|\n"
    body+='\nPer-episode results (violations and relapse numerator/denominator in language/style/format/process order):\n\n'
    body+='| Episode/arm | Success | Integration | Stale | Wrong | Breakage | Violations L/S/F/P | Relapse L/S/F/P |\n|---|---:|---:|---:|---:|---:|---|---|\n'
    for e in endpoints:
        m=e['metrics'];vi='/'.join(str(m['violations'][k]) for k in KINDS);rel=', '.join(f"{m['relapse'][k]['numerator']}/{m['relapse'][k]['denominator']}" for k in KINDS)
        body+=f"|{e['episode']}/{e['arm']}|{e['final_success']}|{e['final_integration']}|{m['stale_execution_rounds']}|{m['wrong_skill_rounds']}|{m['violations']['breakage']}|{vi}|{rel}|\n"
    body+=f"\nActual fixed C4 schedule (including C2 long tails, HTTP, tools/checker and barriers) **{aggregate or 0:.3f} tok/s**. GPU-held **{run['gpu_held_seconds']:.3f}/9000s**, load **{run['load_seconds']:.3f}s**. Served-only conservative projection **{projected} GPU-h**. Formula and all per-episode timing/token costs are in [summary.json](summary.json): prior spend + this run + measured reload +1.25 × [64(max R+max N tokens)+16(max O+max T tokens)] / measured aggregate rate. Max per-arm counts include32-round episodes. Overlapping request seconds are latency, not summed GPU cost. HF recovery remains unmeasured; full check45-inclusive eligibility receives no unmeasured credit.\n"
    body+=f"\nDEV mask trigger **{'MET' if trigger else 'NOT ESTABLISHED'}**, kinds={trigger}; all four kinds and executed-prior-trait denominators are in summary. No masks enabled. T cumulative multi-function re-emissions: {len(per_arm['T']['multi_function_reemissions'])} parseable responses (names listed in summary); capped malformed responses are counted as breakage, not silently repaired.\n"
    body+='\nGold events drive R in DEV only; no fitting, evaluation episode construction or data/bench reads. **package path outcome-unvalidated**. Backend uses qualification image digest `sha256:3dbe092ec5b2cef63b6104d33fa75d6ce53a7870962529ada69f78bbbc38e776`, exact flags/env and request parameters in [registration.json](registration.json). Prior HF divergence5/64 (R1/16) stands; this pilot does not remeasure HF trajectories.\n'
    body+='\n[records.jsonl](records.jsonl) contains same-run v2 records, execution/tolerances, checker and per-call timings; [http/records.jsonl](http/records.jsonl) retains actual streamed token IDs/chunks/usage. [schedule.jsonl](schedule.jsonl) fixes episode lanes and round barriers. Hidden states are **not captured** on vLLM; check45 needs teacher-forced HF prefill. [transcript-manifest.json](transcript-manifest.json) lists the exact final transcript, per-episode output and every prompt+body+EOS hash required, with layer/body-position convention.\n'
    body+='\nStale execution counts rounds with actual executed tools and an observed retired-trait relapse. Per-kind relapse conditions on prior executed trait plus registered opportunity; style measures executed code, format/process measure emitted report traits. Current execution and attempted violations remain separate in records. Empty indentation is not compliant.\n'
    body+='\n[Prewritten registration](prewritten.md) follows unchanged.\n\n'+prereg.read_text()
    (OUT/'README.md').write_text(body)
    print(json.dumps({k:summary[k] for k in ('reading','failures','R_final_success','cost')},indent=2))
if __name__=='__main__':main()
