"""Saved-record-only scoring, no model calls or screening-source reads."""
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P))
import convert as c
spec=importlib.util.spec_from_file_location('check46_score',c.R/'results/quick-checks/check46/evaluate.py')
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
FAMILIES=['cue-less','multi-rule-list','rule+payload','withdraw+replace','bare-value+temporal','task-scoped-override','actually-B']

def admission(records):
    scored=[e.admission_record(r) for r in records]
    out=e.m.metrics.aggregate(scored,'trunk')
    out['go']=bool(out['go'] and (out['overlap']['precision'] or 0)>=.95)
    return out

def family_table(records,task):
    result={}
    for family in FAMILIES:
        sub=[r for r in records if family in c.families(r['input'])]
        if task=='admission':
            scored=[e.admission_record(r) for r in sub]
            tp=sum(r['trunk']['score']['overlap']['tp'] for r in scored);n=sum(r['trunk']['score']['n_gold'] for r in scored)
            misses=[r['input']['id'] for r in scored if r['trunk']['score']['overlap']['fn']]
        else:
            scores=[e.relation_score(r) for r in sub];tp=sum(s['correct'] for s in scores);n=len(scores)
            misses=[r['id'] for r,s in zip(sub,scores) if not s['correct']]
        result[family]=dict(correct=tp,n=n,rate=tp/n if n else None,messages=len(sub),miss_ids=misses)
    return result

def main():
    cost=json.loads((P/'cost.json').read_text());out={'cost':cost,'reading':cost['reading']};allrecords=[]
    complete=cost['reading']=='COMPLETE_PENDING_SCORING'
    for name in ['dev','admission','relations','setup']:
        file=P/(name+'-records.jsonl')
        records=c.rows(file) if file.exists() else []
        allrecords+=records
        if not records:out[name]={'n':0,'measured':False};continue
        if name=='relations':out[name]=e.relation_summary(records)
        elif name=='dev':
            out[name]=dict(n=len(records),operation_set_exact=sum(sorted(json.loads(r['raw']),key=c.digest)==sorted(r['input']['expected_ops'],key=c.digest) if not r['parsed']['failure'] and not r['parsed']['rejected'] else False for r in records))
            out[name]['admission']=admission([r for r in records if 'standing_rules' in r['input']])
            out[name]['relations']=e.relation_summary([r for r in records if 'label' in r['input']])
        else:
            out[name]=admission(records)
            if name=='setup':
                scores=[e.admission_record(r) for r in records];cnt=Counter();hits=Counter()
                for r in scores:
                    gold=r['input']['standing_rules'];cnt.update(s['event'] for s in gold);hits.update(gold[j]['event'] for _,j in r['trunk']['score']['overlap']['pairs'])
                false=sum(r['trunk']['score']['overlap']['fp']>0 for r in scores)
                out[name].update(false_turns=false,events={k:dict(n=cnt[k],recovered=hits[k]) for k in cnt},go=false<=2 and hits['admit']==cnt['admit']==36 and len(records)==96)
        if name in ['admission','relations']:out[name]['families']=family_table(records,name)
    out['latency_seconds']=e.m.metrics.percentiles([r['seconds'] for r in allrecords]) if allrecords else None
    out['parser_failures']=dict(Counter(r['parsed']['failure'] for r in allrecords if r['parsed']['failure']))
    if complete:
        a=out['admission']['go'];rel=out['relations']['go'];s=out['setup']['go']
        latency=max(sorted(r['seconds'] for r in allrecords)[int(.95*(len(allrecords)-1))],0)
        out['reading']='SCREEN-GO' if a and rel and s and latency<=1 else 'PARTIAL' if a!=rel else 'COST-INELIGIBLE' if a and rel and s else 'NO-GO'
    out['complete']=complete;c.write('summary.json',out)
    lines=['\n## Outcome\n',f"**{out['reading']}**. GPU occupied {cost['gpu_seconds']/60:.3f}/60 minutes. Stage: {cost['stage']}.\n"]
    if not complete:
        lines.append('The fixed fit/screen did not complete. Held-out quality, SETUP and per-family accuracy are **unmeasured**, not zero. No quality conclusion about Qwen3-4B is licensed.\n')
        for k in ['load_smoke_seconds','pilot_seconds','train_tokens_per_second','projected_fit_save_seconds','projected_evaluation_seconds']:
            if k in cost:lines.append(f'- {k}: {cost[k]:.3f}\n')
        if cost.get('error'):lines.append(f"\nRuntime error: `{cost['error']}`.\n")
        for task in ['admission','relations']:
            lines.append(f'\n### {task.title()} families\n\n| Family | Correct / denominator | Rate |\n|---|---:|---:|\n')
            for f in FAMILIES:lines.append(f'| {f} | Not evaluated | N/A |\n')
    else:
        a=out['admission'];rel=out['relations'];s=out['setup'];lines.append(f"Admission overlap R {a['overlap']['recall']:.2%}, P {a['overlap']['precision']:.2%}; relations {rel['accuracy']:.2%}, supersedes R {rel['labels']['supersedes']['recall']:.2%}. SETUP {s['events']}, false turns {s['false_turns']}/96.\n")
        for task in ['admission','relations']:
            lines.append(f'\n### {task.title()} families\n\n| Family | Correct / denominator | Rate |\n|---|---:|---:|\n')
            for f,d in out[task]['families'].items():lines.append(f"| {f} | {d['correct']}/{d['n']} | {d['rate']:.2%} |\n" if d['n'] else f'| {f} | 0/0 | N/A |\n')
    text=(P/'README.md').read_text().split('\n## Outcome\n')[0];(P/'README.md').write_text(text+''.join(lines));print(json.dumps(out,indent=2))

if __name__=='__main__':main()
