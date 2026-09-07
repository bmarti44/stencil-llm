"""DEV00/01 pilot4 R and disclosed check40k second look; no fitting."""
import concurrent.futures as cf
import hashlib, importlib.util, json, os, sys, time
from pathlib import Path
ROOT=Path('/home/bmarti44/stencil-llm'); OUT=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT),str(ROOT/'scripts'),str(ROOT/'src')]
def guard(event,args):
    if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)) and '/data/bench' in str(Path(os.fsdecode(args[0])).absolute()):raise RuntimeError('forbidden benchmark access')
sys.addaudithook(guard)
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def write(name,x): (OUT/name).write_text(json.dumps(x,indent=2)+'\n')
def main():
    from tokenizers import Tokenizer
    from transformers import AutoTokenizer
    from scripts import composition_pilot as p
    from stencil.focus import slab
    import focus_check40k as k
    pilot=load('pilot4',ROOT/'results/quick-checks/composition-pilot-4/run.py')
    report=load('report4',ROOT/'results/quick-checks/composition-pilot-4/report.py')
    model=Path('/home/bmarti44/models/qwen3.8-27b-fp8')
    slab.TOKENIZER_PATH=model/'tokenizer.json';slab.qwen_tokenizer.cache_clear()
    tokenizer=Tokenizer.from_file(str(slab.TOKENIZER_PATH))
    tok=AutoTokenizer.from_pretrained(str(model),local_files_only=True)
    # Exact qualification client, only port, EOS set and dynamic cap generalized.
    source=(ROOT/'results/quick-checks/vllm-qual/replay.py').read_text().replace('18081','18087').replace('[151645,151643]','[248046,248044]').replace('len(ids)<=512',"len(ids)<=PARAMS['max_tokens']").replace('len(ids)==512',"len(ids)==PARAMS['max_tokens']")
    namespace={'__name__':'check47_client'};exec(compile(source,'qualified-replay-adapted','exec'),namespace)
    class Client:pass
    client=Client();client.call=namespace['call']; namespace['OUT']=OUT/'http';namespace['OUT'].mkdir(exist_ok=True)
    deadline=json.loads((OUT/'RUNNING.flag').read_text())['deadline']-30
    write('request-parameters.json',namespace['PARAMS'])
    while not (OUT/'READY').exists():
        if not (OUT/'RUNNING.flag').exists():raise RuntimeError('NOT LOADABLE; no model calls')
        time.sleep(2)
    episodes=[slab.generate_episode('dev',i) for i in (0,1)]
    lanes=[p.Lane(OUT,e,'R','dev') for e in episodes]
    start=time.time()
    for index in range(16):
        for lane in lanes:
            lane.prepare(index);lane.gate=dict(allowed=lane.bound<=32256,bounds={'R':lane.bound})
        with cf.ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(lambda l:pilot.one(l,pilot.Decoder(client,tokenizer,deadline,l,index)),lanes))
        print('DEV round',index,'complete',flush=True)
    elapsed=time.time()-start
    rows=[r for l in lanes for r in l.rows]
    stats=report.stats(rows)
    stats.update(schedule_seconds=elapsed,aggregate_tok_s=stats['output_tokens']/elapsed,final_success=sum(l.rows[-1]['oracle_checker_results'][0]['outcome']['success'] for l in lanes),episodes=2,concurrency=2,per_episode={l.episode.episode_id:report.stats(l.rows) for l in lanes})
    write('dev-summary.json',stats)
    namespace['PARAMS']['max_tokens']=768
    tasks=[t for t in k.bank() if t['split']=='eval'];assert len(tasks)==32
    start=time.time()
    def js(pair):
        idx,task=pair;messages=k.j.messages(task,'text-only')
        ids=tok.apply_chat_template(messages,tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False)
        row=client.call('check40k',idx,dict(arm='text-only',round=0,prompt=ids),deadline)
        assert row['complete'],row.get('error')
        text=tok.decode(row['output_token_ids'],skip_special_tokens=True)
        result=dict(task_id=task['id'],messages=messages,output=text,token_ids=row['output_token_ids'],truncated=row['finish_reason']=='length',score=k.score(text,task,row['finish_reason']=='length'),seconds=row['wall_seconds'])
        p.append(OUT/'js-records.jsonl',result);return result
    with cf.ThreadPoolExecutor(max_workers=4) as pool: jsrows=list(pool.map(js,enumerate(tasks)))
    write('js-summary.json',dict(success=sum(r['score']['success'] for r in jsrows),calls=32,seconds=time.time()-start,concurrency=4))
    (OUT/'DONE').write_text('complete')
if __name__=='__main__':main()
