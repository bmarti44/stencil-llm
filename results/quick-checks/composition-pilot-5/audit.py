"""CPU exact-consumer replay and transport/hash/cost audit of pilot 5."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('pilot5_owner', HERE/'run.py')
r=importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)

def main():
    assert r.cmd(['git','-C',str(r.PIN),'rev-parse','HEAD'])==r.SHA
    r.cmd(['git','-C',str(r.PIN),'diff','HEAD','--exit-code'])
    assert str(r.s.__file__).startswith(str(r.PIN))
    checks=0
    for phase,n in [('main',16),('fallback',12)]:
        path=HERE/f'{phase}-records.jsonl'
        if not path.exists(): continue
        rows=[json.loads(line) for line in path.read_text().splitlines()]
        for e in r.s.bank(n_rounds=n):
            for arm in 'TRNO':
                saved=sorted([row for row in rows if row['episode_id']==e.episode_id and row['arm']==arm],key=lambda row:row['turn'])
                if not saved: continue
                assert [row['turn'] for row in saved]==list(range(len(saved)))
                class EndPartial(Exception): pass
                def factory(e,a,i):
                    def decode(rendered):
                        if i>=len(saved): raise EndPartial()
                        row=saved[i]
                        key=f'{phase}/{e.episode_id}/{a}/{i}'
                        http=json.loads((HERE/'local/http'/(key+'.json')).read_text())
                        receipt=json.loads((HERE/'receipts'/(key+'.json')).read_text())
                        assert list(rendered.prompt_ids)==http['request']['prompt']
                        assert http['request']['max_tokens']==1024
                        assert http['request']['stop_token_ids']==[151645,151643]
                        ch=http['response']['choices'][0]
                        assert row['output']==ch['text']
                        ids=row['output_ids']+([] if row['eos'] is None else [row['eos']])
                        assert ids==ch['token_ids'] and len(ids)==http['response']['usage']['completion_tokens']==row['output_tokens']
                        assert row['truncated']==(ch['finish_reason']=='length')
                        assert row['truncated'] or row['eos'] in {151643,151645}
                        assert row['output_sha256']==receipt['output_sha256']==r.hashobj([row['output_ids'],row['eos']])
                        assert receipt['prompt_sha256']==r.hashobj(list(rendered.prompt_ids))
                        assert row['text_sha256']==receipt['text_sha256']==hashlib.sha256(row['output'].encode()).hexdigest()
                        assert row['timing']['seconds']==http['seconds']
                        return r.d.DecodeResult(row['output'],tuple(row['output_ids']),eos=row['eos'],truncated=row['truncated'])
                    return decode
                with tempfile.TemporaryDirectory() as tmp:
                    try: r.d.run_lane(Path(tmp)/'lane',e,arm,factory,n_rounds=n)
                    except EndPartial: pass
                    replay=[json.loads(x) for x in (Path(tmp)/'lane/raw.jsonl').read_text().splitlines()]
                    for old,new in zip(saved,replay,strict=True):
                        for field in ('execution','outcome','output','output_ids','truncated','output_tokens','eos','prompt_tokens'):
                            assert old[field]==new[field],(phase,e.episode_id,arm,old['turn'],field)
                        checks+=1
        summary=json.loads((HERE/f'{phase}-summary.json').read_text())
        if summary['floor']:
            assert summary['floor']==r.s.freeze_t_floor([x for x in rows if x['arm']=='T'],n)
    manifest=json.loads((HERE/'local-hashes.json').read_text())
    for name,meta in manifest.items():
        p=HERE/name
        assert p.stat().st_size==meta['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==meta['sha256']
    life=json.loads((HERE/'lifecycle.json').read_text())
    assert life['gpu_held_seconds']<=5400
    assert not (HERE/'RUNNING.flag').exists()
    gate=json.loads((HERE/'determinism.json').read_text())
    for i in range(8):
        assert gate['outputs'][f'forward-{i}']==gate['outputs'][f'reverse-{i}']
        forward=json.loads((HERE/f'receipts/gate-forward/slab2-dev-{i:02}/R/0.json').read_text())
        reverse=json.loads((HERE/f'receipts/gate-reverse/slab2-dev-{i:02}/R/0.json').read_text())
        assert forward['text_sha256']==reverse['text_sha256']
    receipts=[json.loads(p.read_text()) for p in (HERE/'receipts').rglob('*.json')]
    intervals=sorted([(v['timing']['started'],1) for v in receipts]+[(v['timing']['ended'],-1) for v in receipts])
    active=peak=0
    for _,delta in intervals:
        active+=delta;peak=max(peak,active)
    assert active==0 and peak==4
    assert len(receipts)==checks+16
    result=dict(status='PASS',exact_cpu_round_replays=checks,local_files_hashed=len(manifest),determinism_exact=8,peak_http_concurrency=peak,gpu_held_seconds=life['gpu_held_seconds'])
    r.dump(HERE/'audit.json',result)
    print(json.dumps(result))

if __name__=='__main__': main()
