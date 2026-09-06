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
    compliance=dict(required=0,parsed_edit_attempts=0,executed_edits=0,compliant=0,eligible_edits=0,compliant_edits=0,raw_prefix_eligible_edits=0,raw_prefix_compliant_edits=0,details=[])
    for r in rows:
        d=detail(r)
        if d['round']!=0:continue
        compliance['required']+=1
        expected=int(dict(slab.generate_episode('dev',int(d['episode'].rsplit('-',1)[1])).turns[0].live)['indent'])
        # Inspect emitted fields diagnostically; never feed a prefix to the executor.
        try:
            prefix,end=json.JSONDecoder().raw_decode(r['output'].lstrip())
            for call in prefix.get('calls',[]):
                if call.get('op') in ('edit','replace') and isinstance(call.get('code'),str):
                    ws=slab.indent_widths(call['code'])
                    if ws:
                        compliance['raw_prefix_eligible_edits']+=1
                        compliance['raw_prefix_compliant_edits']+=all(w==expected for w in ws)
        except (ValueError,TypeError,AttributeError):pass
        widths=[];attempts=[]
        try:
            calls=slab.parse_envelope(r['output'])['calls']
            attempts=[c for c in calls if c.get('op') in ('edit','replace')]
            widths=[v for c in attempts for v in slab.indent_widths(c['code'])]
        except (ValueError,KeyError,TypeError,AttributeError):pass
        executed=[c for c in d['execution']['executed'] if c.get('op') in ('edit','replace')]
        ok=bool(executed and widths and not d['outcome']['violations']['style'] and not r['truncated'])
        compliance['parsed_edit_attempts']+=len(attempts);compliance['executed_edits']+=len(executed)
        compliance['compliant']+=ok
        for edit in attempts:
            edit_widths=slab.indent_widths(edit.get('code',''))
            if edit_widths:
                compliance['eligible_edits']+=1
                compliance['compliant_edits']+=bool(edit in executed and all(w==expected for w in edit_widths) and not r['truncated'])
        compliance['details'].append(dict(episode=d['episode'],widths=widths,compliant=ok))
    violations={k:sum(d['outcome']['violations'][k] for d in ds) for k in (*KINDS,'wrong_family','breakage','semantic')}
    cumulative=[];literal_rejections=[]
    for r in rows:
        d=detail(r)
        # Diagnostic attempted JSON extraction only; never feeds parser/executor.
        names=[]
        try:json.loads(r['output'])
        except ValueError:
            try:
                tree=ast.parse(r['output'],mode='eval')
                literals=sorted({str(n.value) for n in ast.walk(tree) if isinstance(n,ast.Constant) and type(n.value) is bool})
                if literals:literal_rejections.append(dict(episode=d['episode'],round=d['round'],literals=literals,executed=bool(d['execution']['executed'])))
            except (ValueError,SyntaxError):pass
        try:
            for c in slab.parse_envelope(r['output']).get('calls',[]):
                if c.get('op') in ('edit','replace'):
                    names.extend(n.name for n in ast.parse(c['code']).body if isinstance(n,ast.FunctionDef))
        except (ValueError,SyntaxError,KeyError,TypeError,AttributeError):pass
        if len(names)>1:cumulative.append(dict(episode=d['episode'],round=d['round'],names=names,op='attempted edits/replaces'))
    pressure=[]
    for episode in sorted({d['episode'] for d in ds}):
        candidates=[row for row in rows if detail(row)['episode']==episode and any(e['action'] in ('supersedes','cancels','completes') for e in row['source_events'])]
        if candidates:
            first=min(candidates,key=lambda row:detail(row)['round']);m=detail(first)['measurements']
            pressure.append(dict(episode=episode,first_retirement_round=detail(first)['round'],prior_own_tokens=m['prior_own_tokens'],prior_100_300_bodies=m['prior_substantial_bodies'],ten_body_pressure_met=m['prior_substantial_bodies']>=10))
    return dict(first_retirement_pressure=pressure,calls=len(rows),executed_responses=sum(bool(d['execution']['executed']) for d in ds),
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
        python_literal_bool_rejections=literal_rejections,multi_function_reemissions=cumulative,
        in_100_300=sum(100<=r['output_token_count']<=300 for r in rows))

def main():
    phases=[OUT]+([OUT/'continuation'] if (OUT/'continuation/run.json').exists() else [])
    rows=[r for phase in phases for r in lines(phase/'records.jsonl')]
    episode_map={}
    for phase in phases:
        for e in lines(phase/'episodes.jsonl'):episode_map[(e['episode'],e['arm'])]=e
    for e in slab.bank('dev'):
        for arm in 'RNTO':
            episode_map.setdefault((e.episode_id,arm),dict(episode=e.episode_id,arm=arm,rounds=0,scheduled_rounds=len(e.turns),complete=False,output_sha256=None,transcript_sha256=None,transcript_path=None,status='UNRUN'))
    episodes=list(episode_map.values())
    observed={(detail(row)['episode'],detail(row)['arm'],detail(row)['round']) for row in rows}
    unsubmitted=[dict(episode=e.episode_id,arm=arm,round=t.index,required=arm!='O',status='UNSUBMITTED',reason='optional O not run' if arm=='O' else 'budget/context stop; see phase events') for e in slab.bank('dev') for arm in 'RNTO' for t in e.turns if (e.episode_id,arm,t.index) not in observed]
    (OUT/'unsubmitted.jsonl').write_text(''.join(p.compact(x)+'\n' for x in unsubmitted))

    stages=[s for phase in phases for s in lines(phase/'stages.jsonl')]
    phase_runs=[json.loads((phase/'run.json').read_text()) for phase in phases]
    run=dict(phase_runs[-1],gpu_held_seconds=sum(r['gpu_held_seconds'] for r in phase_runs),phase_runs=phase_runs)
    gates=[json.loads((phase/'determinism.json').read_text()) for phase in phases]
    gate=dict(passed=all(g['passed'] for g in gates),D=sum(g['D'] for g in gates),calls=sum(g['calls'] for g in gates),phases=gates)
    original_cold={h['index']:h['output_token_ids'] for h in lines(OUT/'http/records.jsonl') if h['pass_name']=='b1_cold'}
    restart_differences=[]
    for phase in phases[1:]:
        for h in lines(phase/'http/records.jsonl'):
            if h['pass_name']=='b1_cold' and h['output_token_ids']!=original_cold[h['index']]:restart_differences.append(dict(phase=str(phase.relative_to(OUT)),index=h['index']))
    gate['restart_differences']=restart_differences
    gate['passed'] &= not restart_differences

    per_arm={a:stats([r for r in rows if detail(r)['arm']==a]) for a in 'RNTO'}
    endpoints=[]
    for ep in episodes:
        selected=sorted([r for r in rows if (detail(r)['episode'],detail(r)['arm'])==(ep['episode'],ep['arm'])],key=lambda r:detail(r)['round'])
        endpoints.append(dict(ep,metrics=stats(selected),final_success=detail(selected[-1])['outcome']['success'] if ep['complete'] else None,
            final_integration=detail(selected[-1])['outcome']['integration'] if ep['complete'] else None))
    for endpoint in endpoints:
        matches=[row for row in rows if (detail(row)['episode'],detail(row)['arm'])==(endpoint['episode'],endpoint['arm'])]
        endpoint['retained_history_sha256']=endpoint['transcript_sha256']
        endpoint['hf_final_transcript_sha256']=None;endpoint['hf_final_transcript_path']=None
        if matches:
            last=max(matches,key=lambda row:detail(row)['round'])
            full=last['rendered_token_ids']+last['output_token_ids']+([] if last['eos'] is None else [last['eos']])
            digest=hashlib.sha256(p.compact(full).encode()).hexdigest()
            assert digest==detail(last)['measurements']['transcript_sha256']
            path=OUT/'hf-transcripts'/endpoint['episode']/(endpoint['arm']+'.json')
            p.write(path,dict(ids=full,sha256=digest,contains_system=True,source_round=detail(last)['round'],body_tokens=len(last['output_token_ids']),eos=last['eos'],complete_episode=endpoint['complete']))
            endpoint['hf_final_transcript_sha256']=digest;endpoint['hf_final_transcript_path']=str(path.relative_to(OUT))
    total_tokens=sum(s['tokens'] for s in stages);wall=sum(s['wall_seconds'] for s in stages)
    aggregate=rate(total_tokens,wall)
    for e in endpoints:
        e['metrics']['allocated_schedule_gpu_seconds']=rate(e['metrics']['output_tokens'],aggregate)
    for s in per_arm.values():
        s['allocated_schedule_gpu_seconds']=rate(s['output_tokens'],aggregate)
    perarm_tokens={a:max((e['metrics']['output_tokens'] for e in endpoints if e['arm']==a and e['complete']),default=None) for a in 'RNTO'}
    prior_paths=['composition-pilot/run.json','composition-pilot-2/run.json','vllm-qual/lifecycle.json']
    prior={s:json.loads((OUT.parent/s).read_text())['gpu_held_seconds'] for s in prior_paths}
    prior['composition-pilot-3/all-starts']=json.loads((OUT.parent/'composition-pilot-3/summary.json').read_text())['cost']['total_pilot3_gpu_seconds']
    pilot4_total=run['gpu_held_seconds']
    initial=json.loads((OUT.parent/'vllm-qual/initial-lifecycle.json').read_text())
    prior['vllm-qual/initial-lifecycle.json']=initial['gpu_held_seconds']
    weighted=64*(perarm_tokens['R']+perarm_tokens['N'])+16*(perarm_tokens['T']+perarm_tokens['O']) if all(v is not None for v in perarm_tokens.values()) else None
    projected=(sum(prior.values())+run['gpu_held_seconds']+run.get('load_seconds',0)+1.25*weighted/aggregate)/3600 if weighted and aggregate else None
    known_weighted=64*(perarm_tokens['R']+perarm_tokens['N'])+16*perarm_tokens['T'] if all(perarm_tokens[a] is not None for a in 'RNT') else None
    projection_floor=(sum(prior.values())+run['gpu_held_seconds']+run.get('load_seconds',0)+1.25*known_weighted/aggregate)/3600 if known_weighted and aggregate else None
    failures=[]
    if not gate['passed']:failures.append('D !=0 or incomplete determinism')
    if sum(e['complete'] and e['arm'] in 'RNT' for e in endpoints)!=24:failures.append('incomplete required R/N/T DEV trajectories')
    r=per_arm['R'];c=r['round0_indent']
    if c['required']!=8 or c['compliant']<4 or not c['eligible_edits'] or c['compliant_edits']/c['eligible_edits']<.5:failures.append('R round0 indentation <50% or incomplete')
    for a in 'RNT':
        s=per_arm[a]
        if not s['calls'] or s['executed_responses']/s['calls']<.9:failures.append(a+' executed-call rate <90%')
        if not s['calls'] or s['truncated']/s['calls']>.02:failures.append(a+' truncation >2%')
    r_success=sum(e['final_success'] is True for e in endpoints if e['arm']=='R')
    if r_success<5:failures.append('R final success <5/8')
    eligible_kinds=[k for k,v in r['relapse'].items() if len(v['opportunity_episodes'])>=2]
    if len(eligible_kinds)<2:failures.append('R executed-trait opportunities in >=2 episodes for <2 kinds')
    if not rows or max(r['input_token_count'] for r in rows)>32768-512:failures.append('context missing or exceeds32256')
    if projection_floor is not None and projection_floor>12:failures.append('registered projection >12h even setting unmeasured O cost to zero')
    elif projected is None or projected>12:failures.append('served cost projection unmeasured or >12h')
    failures.append('check45 HF teacher-forced recovery cost unmeasured (prewritten full-cost condition)')
    trigger=[]
    for k,v in r['relapse'].items():
        if v['denominator']>=20 and v['numerator']/v['denominator']>=.15 and len(v['relapsing_episodes'])>=2 and len(per_arm['O']['relapse'][k]['relapsing_episodes'])>=2:trigger.append(k)
    manifest=dict(hidden_states_captured=False,required='Check45 HF teacher-forced prefill; layers8/16/24/32/40; last-prompt and mean over all body positions, EOS excluded; forward last body token even at cap. HF-conditioned activations, not vLLM hidden states.',
        hash_encoding='SHA256 of compact JSON integer list',
        episodes=[{k:e[k] for k in ('episode','arm','complete','output_sha256','retained_history_sha256','transcript_path','hf_final_transcript_sha256','hf_final_transcript_path')} for e in endpoints],
        calls=[dict(episode=detail(r)['episode'],arm=detail(r)['arm'],round=detail(r)['round'],
            prompt_sha256=detail(r)['measurements']['prompt_sha256'],output_sha256=detail(r)['measurements']['output_sha256'],
            transcript_sha256=detail(r)['measurements']['transcript_sha256'],body_tokens=len(r['output_token_ids']),eos=r['eos'],truncated=r['truncated']) for r in rows])
    p.write(OUT/'transcript-manifest.json',manifest)
    comparison=[]
    indexed={(detail(x)['episode'],detail(x)['arm'],detail(x)['round']):x for x in rows}
    for (episode,arm,index),rr in indexed.items():
        if arm!='R' or (episode,'O',index) not in indexed:continue
        oo=indexed[(episode,'O',index)]
        a=rr['output_token_ids']+([] if rr['eos'] is None else [rr['eos']])
        b=oo['output_token_ids']+([] if oo['eos'] is None else [oo['eos']])
        first=next((i for i,(x,y) in enumerate(zip(a,b)) if x!=y),min(len(a),len(b))) if a!=b else None
        comparison.append(dict(episode=episode,round=index,prompt_identical=rr['rendered_token_ids']==oo['rendered_token_ids'],
            output_identical=a==b,first_difference=first))
    p.write(OUT/'R-O-repeat.json',comparison)
    summary=dict(reading='INELIGIBLE' if failures else 'ELIGIBLE',failures=failures,per_arm=per_arm,endpoints=endpoints,
        R_final_success=r_success,R_opportunity_kinds=eligible_kinds,run=run,determinism=gate,
        R_O_repeat=dict(calls=len(comparison),same_prompt=sum(c['prompt_identical'] for c in comparison),same_output=sum(c['output_identical'] for c in comparison)),
        cost=dict(aggregate_tok_s=aggregate,stage_wall_seconds=wall,tokens=total_tokens,prior_seconds=prior,
            max_episode_tokens=perarm_tokens,weighted_future_tokens=weighted,served_projection_hours=projected,
            known_RNT_projection_floor_hours=projection_floor,HF_recovery_seconds=None,full_projection_hours=None,charged_pilot_hours=pilot4_total/3600,total_pilot4_gpu_seconds=pilot4_total),
        DEV_mask_trigger=dict(met=bool(trigger),kinds=trigger,requires_state_audit=True),
        unsubmitted_required=sum(x['required'] for x in unsubmitted),unsubmitted_optional=sum(not x['required'] for x in unsubmitted),
        output_band='100-300 diagnostic, unchanged',backend='qualified vLLM; package path outcome-unvalidated')
    trait_summary_path=OUT/'trait-swap/summary.json'
    if trait_summary_path.exists():summary['trait_swap']=json.loads(trait_summary_path.read_text())
    p.write(OUT/'summary.json',summary)
    # Keep preregistration byte-for-byte as its own artifact, before updating README.
    prereg=OUT/'prewritten.md'
    if not prereg.exists():prereg.write_bytes((OUT/'README.md').read_bytes())
    projection_text=f'{projected:.3f}' if projected is not None else 'UNAVAILABLE'
    floor_text=f'{projection_floor:.3f}' if projection_floor is not None else 'UNAVAILABLE'
    body='# Composition pilot 4 — '+summary['reading']+'\n\n'
    body+=f"Completed {len(rows)} calls; R final success **{r_success}/8**. "
    body+=f"Round-0 R indent **{c['compliant']}/{c['required']} required responses**; strictly executed/parsed eligible subset **{c['compliant_edits']}/{c['eligible_edits']}**; diagnostic emitted JSON-prefix code **{c['raw_prefix_compliant_edits']}/{c['raw_prefix_eligible_edits']}**. Prefix inspection never repairs or executes a rejected response. Determinism **D={gate['D']}**, {gate['calls']} calls across completed starts.\n\n"
    body+='Failed/unmeasured gates: '+ '; '.join(failures)+'.\n\n'
    body+='| Arm | Calls executed | Caps | Final success | Stale execution | Wrong skill | Breakage | Decode tok/s | s/call |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|\n'
    for a,s in per_arm.items():
        finals=sum(e['final_success'] is True for e in endpoints if e['arm']==a);n=sum(e['complete'] for e in endpoints if e['arm']==a)
        dec=f"{s['decode_tok_s']:.3f}" if s['decode_tok_s'] is not None else '—'
        latency=f"{s['seconds_per_call']:.3f}" if s['seconds_per_call'] is not None else '—'
        label=a if s['calls'] else a+' (UNRUN)'
        body+=f"|{label}|{s['executed_responses']}/{s['calls']}|{s['truncated']}|{finals}/{n}|{s['stale_execution_rounds']}|{s['wrong_skill_rounds']}|{s['violations']['breakage']}|{dec}|{latency}|\n"
    body+='\nPer-episode results (violations and relapse numerator/denominator in language/style/format/process order):\n\n'
    body+='| Episode/arm | Success | Integration | Stale | Wrong | Breakage | Violations L/S/F/P | Relapse L/S/F/P |\n|---|---:|---:|---:|---:|---:|---|---|\n'
    for e in endpoints:
        m=e['metrics']
        if not m['calls']:
            body+=f"|{e['episode']}/{e['arm']}|UNRUN|—|—|—|—|—|—|\n"
            continue
        vi='/'.join(str(m['violations'][k]) for k in KINDS);rel=', '.join(f"{m['relapse'][k]['numerator']}/{m['relapse'][k]['denominator']}" for k in KINDS)
        success=e['final_success'] if e['complete'] else 'INCOMPLETE'
        integration=e['final_integration'] if e['complete'] else '—'
        body+=f"|{e['episode']}/{e['arm']}|{success}|{integration}|{m['stale_execution_rounds']}|{m['wrong_skill_rounds']}|{m['violations']['breakage']}|{vi}|{rel}|\n"
    body+='\nPer-episode timing and cost allocation (observed calls only). Allocated seconds = output tokens / measured whole-schedule aggregate rate; this partitions shared schedule cost by tokens, rather than measuring isolated episode GPU use. Startup/checks/cleanup are charged separately in the total.\n\n'
    body+='| Episode/arm | Calls | Tokens | Decode tok/s | Seconds/call | Allocated schedule seconds |\n|---|---:|---:|---:|---:|---:|\n'
    for e in endpoints:
        m=e['metrics']
        if m['calls']:
            body+=f"|{e['episode']}/{e['arm']}|{m['calls']}|{m['output_tokens']}|{m['decode_tok_s']:.3f}|{m['seconds_per_call']:.3f}|{m['allocated_schedule_gpu_seconds']:.3f}|\n"
    body+=f"\nMain-run measurements: determinism D={gate['D']}; maximum actual context {max((row['input_token_count'] for row in rows),default=0)} <=32256; executed-trait opportunities in at least two R episodes for kinds {eligible_kinds}. These do not override the failed gates.\n"
    body+=f"\nActual fixed C4 schedule (including C2 long tails, HTTP, tools/checker and barriers) **{aggregate or 0:.3f} tok/s**. GPU-held **{pilot4_total:.3f}/9000s** (all starts), load **{run.get('load_seconds',0):.3f}s**. Served-only conservative projection **{projection_text} GPU-h**. Formula and all per-episode timing/token costs are in [summary.json](summary.json): prior spend + this run + measured reload +1.25 × [64(max R+max N tokens)+16(max O+max T tokens)] / measured aggregate rate. Max per-arm counts include32-round episodes. Overlapping request seconds are latency, not summed GPU cost. The known R/N/T contribution gives a registered-projection floor of **{floor_text}h** even setting O cost to zero; this is a lower bound on that conservative projection, not a complete workload forecast. HF recovery remains unmeasured; full check45-inclusive eligibility receives no unmeasured credit.\n"
    body+=f"\nDEV mask trigger **{'MET' if trigger else 'NOT ESTABLISHED'}**, kinds={trigger}; all four kinds and executed-prior-trait denominators are in summary. No masks enabled. T multi-function emitted responses under the amended parser (edit or replace; descriptive): {len(per_arm['T']['multi_function_reemissions'])} parseable responses (names listed in summary); capped malformed responses are counted as breakage, not silently repaired.\n"
    body+='\nRejected Python-literal boolean residues (outside quoted code strings): '+str({a:len(v['python_literal_bool_rejections']) for a,v in per_arm.items()})+'. These are CPU classifications of literal journaled outputs, not parser repairs.\n'
    body+='\nGold events drive R in DEV only; no fitting, evaluation episode construction or data/bench reads. **package path outcome-unvalidated**. Backend uses qualification image digest `sha256:3dbe092ec5b2cef63b6104d33fa75d6ce53a7870962529ada69f78bbbc38e776`, exact flags/env and request parameters in [registration.json](registration.json). Prior HF divergence5/64 (R1/16) stands; this pilot does not remeasure HF trajectories.\n'
    body+='\n[record shards](artifact-manifest.json) contain same-run v2 records, execution/tolerances, checker and per-call timings; local http/records.jsonl (size/SHA256 in artifact-manifest.json) retains actual streamed token IDs/chunks/usage. [schedule.jsonl](schedule.jsonl) fixes episode lanes and round barriers. Hidden states are **not captured** on vLLM; check45 needs teacher-forced HF prefill. [transcript-manifest.json](transcript-manifest.json) lists the full HF final-input files under hf-transcripts/ (including system prefix), per-episode output and every prompt+body+EOS hash required, with layer/body-position convention. The separate retained-history hashes describe session state without the system prefix; those files alone are not HF prefill inputs.\n'
    body+=f"\n[Unsubmitted calls](unsubmitted.jsonl): {summary['unsubmitted_required']} required and {summary['unsubmitted_optional']} optional. UNRUN/None endpoints are unavailable, not observed failures or zeros. All planned episodes remain in eligibility accounting.\n"
    body+='\nStale execution counts rounds with actual executed tools and an observed retired-trait relapse. Per-kind relapse conditions on prior executed trait plus registered opportunity; style measures executed code, format/process measure emitted report traits. Current execution and attempted violations remain separate in records. Empty indentation is not compliant.\n'
    # Historical pilot3 continuation does not apply.
    if 'trait_swap' in summary:
        ts=summary['trait_swap']
        body+=f"\nConditional lexical style screen: **{ts['reading']}**, {ts['responses']}/8 compliant required responses, {ts['compliant_edits']}/{ts['eligible_executed_edits']} eligible executed edits. This is round-zero competence only and does not change pilot3 ineligibility. [Style records, CPU witnesses, audit and summary](trait-swap/README.md); full HF input hashes are in trait-swap/transcripts.jsonl. Its {ts['gpu_held_seconds']:.3f}s is included in the total above.\n"
    body+='\nValidation: [50 targeted DEV-only tests](validation-all-amendments.log), [96-call CPU smoke](smoke.json), the original qualification adapter EOS/cap checks. The final [CPU audit](audit.json) replays each saved actual prompt, controller state, output, execution and checker result and verifies backend identity, determinism, transcript hashes and cleanup. No full pytest suite or evaluation episodes were run.\n'
    body+='\n[Prewritten registration](prewritten.md) follows unchanged.\n\n'+prereg.read_text()
    (OUT/'README.md').write_text(body)
    print(json.dumps({k:summary[k] for k in ('reading','failures','R_final_success','cost')},indent=2))
if __name__=='__main__':main()
