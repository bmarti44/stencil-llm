"""Replay saved records through the frozen consumer and verify literal lifecycle."""
import collections
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'results/quick-checks/check49'


def main():
    from transformers import AutoTokenizer
    spec=importlib.util.spec_from_file_location('check49',ROOT/'scripts/focus_check49.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    data=json.loads((OUT/'data.json').read_text())
    summary=json.loads((OUT/'summary.json').read_text())
    rows=[json.loads(x) for x in (OUT/'records.jsonl').read_text().splitlines()]
    by={r['id']:r for r in rows}
    tasks={t['id']:t for t in data['fit']+data['setup']+[t for e in data['episodes'] for t in e['tasks']]+data['sentinels']}
    tok=AutoTokenizer.from_pretrained(m.BASE,local_files_only=True)
    assert len(rows)==len(by)==272
    discrepancies=[]
    for r in rows:
        t=tasks[r['task_id']]
        if 'cases' in t:
            s=m.execute(t,r['text'])
            for key in ['syntax','semantics','language','presentation']:
                if s[key]!=r[key]: discrepancies.append([r['id'],key,s[key],r[key]])
        else:
            try: sem=json.dumps(json.loads(r['text']))==json.dumps(t['expected'])
            except ValueError: sem=False
            if sem!=r['semantics']: discrepancies.append([r['id'],'sentinel_semantics',sem,r['semantics']])
        ids=tok.encode(m.render(tok,r['messages']),add_special_tokens=False)
        assert ids==r['input_ids'],r['id']
        assert tok.decode(r['token_ids'],skip_special_tokens=True)==r['text']
        assert len(r['token_ids'])<=96
        assert (len(r['token_ids'])==96 and r['token_ids'][-1]!=tok.eos_token_id)==r['truncated']
        assert r['prefill_seconds'] is not None and r['decode_seconds'] is not None
    for ep in data['episodes']:
        a=ep['initial'];b=m.MODES[1-m.MODES.index(a)]
        schedule=[a,a,b,a,None]
        for arm in ['M','T','X']:
            hist=[]
            for i,stage in enumerate(m.STAGES):
                if i==1: hist+=m.NEUTRAL
                r=by[f'episode/{ep["id"]}/{arm}/{stage}']
                assert r['messages']==m.messages(ep['tasks'][i],hist,schedule[i] if arm=='T' else None)
                expected_mode=schedule[i] if arm=='M' else m.MODES[1-m.MODES.index(schedule[i])] if arm=='X' and schedule[i] else None
                assert r['mode']==expected_mode
                assert r['expected']==schedule[i]
                hist += [dict(role='user',content=ep['tasks'][i]['prompt']),dict(role='assistant',content=r['text'])]
        assert by[f'cold/{ep["id"]}']['messages']==m.messages(ep['tasks'][5],m.NEUTRAL)
        assert by[f'cold/{ep["id"]}']['mode']==a
        assert by[f'fresh/{ep["id"]}']['messages']==m.messages(ep['tasks'][4])
        assert by[f'replay/{ep["id"]}']['messages']==by[f'episode/{ep["id"]}/M/CLEAR']['messages']
    analysis=m.analyze(rows,summary['parity'])
    assert analysis['bars']==summary['bars']
    assert not discrepancies,discrepancies
    fits=[json.loads(x) for x in (OUT/'fit.jsonl').read_text().splitlines()]
    assert len(fits)==32 and all(x['grad_norm']>0 for x in fits)
    adapter_files=json.loads((OUT/'adapter-manifest.json').read_text())
    assert all(m.sha(ROOT/p)==x['sha256'] for p,x in adapter_files.items())
    assert all(m.sha(ROOT/p)==h for p,h in json.loads((OUT/'contract.json').read_text())['frozen_files'].items())
    groups={}
    for arm in ['M','T','X']:
        active=[r for r in rows if r['id'].startswith('episode/') and f'/{arm}/' in r['id'] and not r['id'].endswith('/CLEAR')]
        groups[arm]=dict(n=len(active),language=sum(r['language']==r['expected'] for r in active),semantics=sum(r['semantics'] for r in active),joint=sum(r['success'] for r in active),syntax_failures=sum(not r['syntax'] for r in active),truncations=sum(r['truncated'] for r in active),presentation_failures=sum(not r['presentation'] for r in active),by_stage={s:dict(language=sum(r['language']==r['expected'] for r in active if r['id'].endswith('/'+s)),joint=sum(r['success'] for r in active if r['id'].endswith('/'+s))) for s in m.STAGES[:4]})
    episodes=[]
    for ep in data['episodes']:
        row=dict(episode=ep['id'],family=ep['tasks'][0]['family'],initial=ep['initial'])
        for arm in ['M','T','X']:
            row[arm]=[by[f'episode/{ep["id"]}/{arm}/{s}']['success'] for s in m.STAGES[:4]]
        row['cold']=by[f'cold/{ep["id"]}']['success']
        episodes.append(row)
    output=dict(record_replays=len(rows),literal_history_checks=180,discrepancies=discrepancies,active=groups,episodes=episodes,adapter_hashes_verified=len(adapter_files),prefill_seconds=sum(r['prefill_seconds'] for r in rows),decode_seconds=sum(r['decode_seconds'] for r in rows),artifacts_bytes=sum(p.stat().st_size for p in OUT.iterdir() if p.is_file()))
    m.write(OUT/'audit.json',output)
    print(json.dumps(output,indent=2))


if __name__=='__main__': main()
