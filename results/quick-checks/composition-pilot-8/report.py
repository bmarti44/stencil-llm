"""CPU saved-receipt audit and descriptive report; never launches inference."""
import argparse
import hashlib
import json
from pathlib import Path
from math import comb

from stencil.focus import slab2_v2 as s


def main():
    ap=argparse.ArgumentParser();ap.add_argument('out');ap.add_argument('--pilot',action='store_true');args=ap.parse_args()
    out=Path(args.out)
    rows=[json.loads(line) for arm in 'RNTQ' for line in (out/f'records-{arm}.jsonl').read_text().splitlines()]
    summary=json.loads((out/'summary.json').read_text())
    life=json.loads((out/'lifecycle.json').read_text())
    groups=json.loads((out/'groups.json').read_text()) if (out/'groups.json').exists() else []
    audited=0;tokens=0;prompt_tokens=0;byarm={a:dict(attempts=0,tokens=0,repairs=0,syntax_before=0,syntax_after=0,indent_after=0,protocol_breakage_episodes=0,final_integration=0) for a in 'RNTQ'}
    for row in rows:
        arm=row['arm'];m=byarm[arm]
        for i,attempt in enumerate(row['attempts'],1):
            http=out/'local/http'/f'main-attempt{i}'/row['episode_id']/arm/f"{row['turn']}.json"
            receipt=json.loads(http.read_text());resp=receipt['response'];c=resp['choices'][0]
            assert c['text']==attempt['output']
            ids=attempt['output_ids']+([attempt['eos']] if attempt['eos'] is not None else [])
            assert c['token_ids']==ids
            assert (c['finish_reason']=='length')==attempt['truncated']
            assert len(ids)==resp['usage']['completion_tokens']
            assert len(receipt['request']['prompt'])+2048<=32768
            audited+=1;tokens+=len(ids);m['tokens']+=len(ids);m['attempts']+=1
            prompt_tokens+=len(receipt['request']['prompt'])
        final=row['attempts'][-1]
        for key in ('output','output_ids','eos','truncated','execution'):
            assert final[key]==row[key], (row['episode_id'],row['turn'],key)
        assert row['repairs_used']==len(row['attempts'])-1
        m['repairs']+=row['repairs_used']
        m['syntax_before']+=row['attempts'][0]['execution'].get('category')=='syntax_error'
        m['syntax_after']+=row['execution'].get('category')=='syntax_error'
        m['indent_after']+=row['execution'].get('syntax_type') in ('IndentationError','TabError')
    for arm,m in byarm.items():
        m['protocol_breakage_episodes']=len({r['episode_id'] for r in rows if r['arm']==arm and r['outcome']['diagnostics']['breakage']})
        m['final_integration']=sum(r['turn']==15 and r['outcome']['integration'] for r in rows if r['arm']==arm)
    episodes=s.bank('dev' if args.pilot else 'eval')
    if args.pilot:
        rebuilt=s.pilot_reading(rows,episodes,deterministic=not json.loads((out/'determinism.json').read_text())['mismatches'])
    else:
        rebuilt=s.larger_reading(rows,episodes,[e.episode_id for e in episodes[:16]],cpu_control=True,calibrated=True)
    assert rebuilt==summary, 'frozen reading differs'
    lane_seconds={a:sum(g['seconds'] for g in groups if g['arm']==a)/8 for a in 'RNTQ'} if args.pilot and len(groups)==8 else None
    projection=(json.loads((out/'ready.json').read_text())['load_seconds']+1.25*(64*sum(lane_seconds[a] for a in 'RNT')+16*lane_seconds['Q'])+1200)/3600 if lane_seconds else None
    report=dict(records=len(rows),attempts_audited=audited,main_output_tokens=tokens,main_prompt_tokens=prompt_tokens,per_arm=byarm,gpu_held_hours=life['gpu_held_seconds']/3600,lane_seconds=lane_seconds,projected_full_gpu_hours=projection,frozen_reading_equal=True)
    (out/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
    lines=[('Fit-on: none; development-on: the eight DEV episodes only; evaluated-on: none; fresh64 unopened. Prior spent-bank audits informed the protocol.' if args.pilot else 'Fit-on: none; development-on: the eight DEV episodes only; evaluated-on: fresh successor bank, one model pass; prior failure audits informed protocol.'),'',f"# Amendment 6 — {summary['reading']}",'',f"{len(rows)} scheduled records; {audited} initial/repair HTTP responses audited against text, generated IDs, EOS and cap accounting. Frozen reading reproduces exactly. GPU held {life['gpu_held_seconds']/3600:.4f} hours.",'',f"Failed items: {', '.join(summary['failures']) or 'none'}.",'','| Arm | Repairs | Initial syntax errors | Surviving syntax / indent | Broken episodes | Final semantic integration |','|---|---:|---:|---:|---:|---:|']
    for a,m in byarm.items():lines.append(f"| {a} | {m['repairs']} | {m['syntax_before']} | {m['syntax_after']} / {m['indent_after']} | {m['protocol_breakage_episodes']} | {m['final_integration']} |")
    lines+=['','Breakage excludes semantic wrong values and runtime test exceptions. Final semantic integration is descriptive; it is not delivery adherence. Repairs are counted per round; two failures in one round are one final breakage.','', '| Family | Episodes | R wins / N wins / ties | Gain | One-sided p | Holm p | Missing-as-failure gain |','|---|---:|---:|---:|---:|---:|---:|']
    for key in ('delivery','format','indent'):
        f=summary['primary']['families'][key]
        lines.append(f"| {key} | {f['n']} | {f['wins']}/{f['losses']}/{f['ties']} | {f['mean_gain']} | {f['p']:.9g} | {f['holm_p']:.9g} | {f['strict_failed_attempts']['mean_gain']} |")
    lines+=['','Delivery is the unchanged predeclared primary: common parsed change-round writes, within-episode averaging before an exact one-sided R>N sign, Holm over all three families. Missingness and per-episode denominators are in summary.json.','', 'The old format result tolerates only ONE adversarial flip before losing Holm significance. That frozen result remains FAIL and is not rescored here.']
    harm=summary['harm_calibration' if args.pilot else 'harm']
    lines+=['','| Harm contrast | Common-attempt episodes | Greater / lower / ties | Holm p | Coverage | Harm signal |','|---|---:|---:|---:|---|---|']
    for a,c in harm['contrasts'].items():lines.append(f"| {a}:N | {c['n']} | {c['wins']}/{c['losses']}/{c['ties']} | {c['holm_p']:.9g} | {c['coverage']} | {c['signal']} |")
    lines+=['','Conditional harm uses common attempted indent changes and one averaged episode sign. Noncompliance cannot supply a safe observation; both contrasts need 75% episode coverage. Passing is not proof of no harm or noninferiority. T is the block-free reminder negative control; it can still suffer reminder-induced failures.']
    if projection is not None:lines+=['',f'Measured full-run projection, including25% main reserve and1200s controls/cleanup: {projection:.4f} GPU-hours.']
    if (out/'reproducibility.json').exists():
        r=json.loads((out/'reproducibility.json').read_text());lines+=['',f"Cross-run control: {r['divergent']}/{r['payloads']} divergent, {r['any_divergence_episodes']}/8 DEV episodes with any divergence. Fixed pilot7 R payloads, descriptive clustered control; not universal reproducibility."]
    elif args.pilot:lines+=['','The registered cross-run40-payload control belongs to the full successor run. Pilot8 ran its within-container forward/reverse determinism control.']
    lines+=['','Claim ceiling: request-time restatement on one frozen trunk and authored procedural distribution. No superiority-to-prose, removed-stale-influence, generalized coding improvement, autonomous admission or actuator claim. Original system example and accumulated history confounds remain.','', 'Artifacts: [registration](REGISTRATION.md), [summary](summary.json), [audit](audit.json), records-R/N/T/Q.jsonl, local-hashes.json and pin-verification.json. Raw HTTP/journal evidence is local and hash-indexed.']
    (out/('README.md' if args.pilot else 'RESULTS.md')).write_text('\n'.join(lines)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
