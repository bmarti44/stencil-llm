"""Frozen DEV-only streaming token-ID replay; write each call immediately."""
import concurrent.futures, json, threading, time, urllib.request
from pathlib import Path
OUT=Path('/home/bmarti44/stencil-llm/results/quick-checks/vllm-qual')
URL='http://127.0.0.1:18081'
LOCK=threading.Lock()
PARAMS=dict(model='/model',temperature=0,top_p=1,top_k=-1,min_p=0,repetition_penalty=1,frequency_penalty=0,presence_penalty=0,max_tokens=512,stop_token_ids=[151645,151643],ignore_eos=False,logprobs=None,return_token_ids=True,stream=True,stream_options={'include_usage':True},seed=0)
def metrics(name):
    with urllib.request.urlopen(URL+'/metrics',timeout=10) as r:(OUT/name).write_bytes(r.read())
def call(pass_name, index, frozen, deadline):
    row=dict(pass_name=pass_name,index=index,arm=frozen['arm'],round=frozen['round'],prompt_token_ids=frozen['prompt'],output_token_ids=[],chunks=[],started=time.time())
    t=time.perf_counter();first=None;last=None
    try:
        if time.time()>deadline-90:raise TimeoutError('cooperative deadline: no new call')
        req=urllib.request.Request(URL+'/v1/completions',data=json.dumps(dict(PARAMS,prompt=frozen['prompt'])).encode(),headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=min(180,deadline-time.time())) as response:
            for line in response:
                if time.time()>deadline:raise TimeoutError('cooperative deadline')
                if not line.startswith(b'data: '):continue
                payload=line[6:].strip()
                if payload==b'[DONE]':row['done']=True;break
                chunk=json.loads(payload);now=time.perf_counter()
                row['chunks'].append({'elapsed':now-t,'response':chunk})
                if 'error' in chunk:raise RuntimeError(chunk['error'])
                if chunk.get('usage'):row['usage']=chunk['usage']
                for c in chunk.get('choices',[]):
                    assert c['index']==0
                    if c.get('prompt_token_ids') is not None:assert c['prompt_token_ids']==frozen['prompt']
                    ids=c.get('token_ids');assert ids is not None
                    if ids:
                        if first is None:first=now;row['first_chunk_tokens']=len(ids)
                        last=now;row['output_token_ids'].extend(ids)
                    if c.get('finish_reason') is not None:
                        row['finish_reason']=c['finish_reason'];row['stop_reason']=c.get('stop_reason')
        ids=row['output_token_ids'];assert row.get('done') and ids and len(ids)<=512
        assert row['usage']['completion_tokens']==len(ids)
        assert row['usage']['prompt_tokens']==len(frozen['prompt'])
        assert not any(x in [151645,151643] for x in ids[:-1])
        if row['finish_reason']=='stop':assert ids[-1] in [151645,151643]
        else:assert row['finish_reason']=='length' and len(ids)==512
        row['complete']=True
    except Exception as e:row['error']=repr(e);row['complete']=False
    row['wall_seconds']=time.perf_counter()-t
    row['ttft_seconds']=first-t if first else None
    row['decode_seconds']=last-first if first and last else None
    row['decode_tokens']=len(row['output_token_ids'])-row.get('first_chunk_tokens',0)
    row['decode_tok_s']=row['decode_tokens']/row['decode_seconds'] if row['decode_seconds'] else None
    with LOCK:
        with (OUT/'records.jsonl').open('a') as f:f.write(json.dumps(row)+'\n');f.flush()
        print(pass_name,index,len(row['output_token_ids']),row.get('decode_tok_s'),row.get('error'),flush=True)
    return row

def main():
    frozen=json.loads((OUT/'frozen.json').read_text());assert len(frozen)==64
    assert all(len(x['output_ids'])<=512 and x['prompt'] for x in frozen)
    assert not (OUT/'records.jsonl').exists()
    (OUT/'request-parameters.json').write_text(json.dumps(PARAMS,indent=2))
    deadline=json.loads((OUT/'RUNNING.flag').read_text())['deadline']-90
    while not (OUT/'READY').exists():
        if not (OUT/'RUNNING.flag').exists():raise RuntimeError('server failed')
        time.sleep(2)
    passes=[]
    try:
        for name,concurrency in [('b1_first',1),('b1_repeat',1),('b4',4),('b8',8)]:
            metrics(name+'-before.prom');start=time.time()
            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
                rows=list(pool.map(lambda pair:call(name,*pair,deadline),enumerate(frozen)))
            end=time.time();metrics(name+'-after.prom')
            passes.append(dict(name=name,concurrency=concurrency,start=start,end=end,wall_seconds=end-start,complete=sum(r['complete'] for r in rows),tokens=sum(len(r['output_token_ids']) for r in rows)))
            (OUT/'passes.json').write_text(json.dumps(passes,indent=2))
            if not all(r['complete'] for r in rows):break
    finally:(OUT/'DONE').write_text('replay finished')
if __name__=='__main__':main()
