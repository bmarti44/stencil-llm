"""Single fixed LoRA screen; cooperative deadlines, no process signals."""
import gc
import importlib.util
import json
import math
import os
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

P=Path(__file__).resolve().parent
sys.path.insert(0,str(P))
import convert as c
R=c.R
spec=importlib.util.spec_from_file_location('check46_parser',R/'results/quick-checks/check46/run.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
SCHEMA=json.loads((R/'results/quick-checks/check46/schema.json').read_text())
SCHEMA['items']['properties']['op']['enum'].remove('none')
MODEL=R/'models/qwen3-4b-hf'
ADAPTER=R/'data/classifier/model/updater-4b-v1'
HELD=[R/'data/classifier/heldout'/f'fable-{n}-heldout-4.jsonl' for n in ['admission','relations']]
MODULES=['q_proj','k_proj','v_proj','o_proj','gate_proj','up_proj','down_proj']
BATCH=4
EVAL_BATCH=8
CAP=512

class BudgetStop(Exception):pass

def log(obj):print(json.dumps(obj),flush=True)

def check(deadline,reserve=0):
    if time.monotonic()+reserve>=deadline:raise BudgetStop('phase deadline reserve reached')

def parse(raw,row,finish):
    out=m.parse(raw,row,finish)
    if not out['failure']:
        if any(o['op']=='none' for o in json.loads(raw)):out['failure']='schema_none_forbidden';out['accepted']=[]
    return out

def batch_tensors(tok,records):
    import torch
    encoded=[c.tokens(tok,r) for r in records];n=max(len(a)+len(b) for a,b in encoded)
    assert n<=768
    ids=[];labels=[];mask=[]
    for a,b in encoded:
        pad=n-len(a)-len(b);ids.append(a+b+[tok.pad_token_id]*pad);mask.append([1]*(len(a)+len(b))+[0]*pad);labels.append([-100]*len(a)+b+[-100]*pad)
    assert all(any(v!=-100 for v in row) for row in labels)
    return {k:torch.tensor(v,device='cuda') for k,v in [('input_ids',ids),('attention_mask',mask),('labels',labels)]}

def infer(model,tok,td,rows,name,deadline):
    import torch
    from transformers import StoppingCriteria,StoppingCriteriaList
    from lmformatenforcer import JsonSchemaParser
    from grammar import build_transformers_prefix_allowed_tokens_fn
    class Deadline(StoppingCriteria):
        def __call__(self,input_ids,scores,**kwargs):return time.monotonic()>=deadline-3
    records=[];start=time.monotonic();path=P/(name+'-records.jsonl')
    with path.open('x') as f:
        for offset in range(0,len(rows),EVAL_BATCH):
            check(deadline,5)
            batch=rows[offset:offset+EVAL_BATCH];prompts=[];vis=[]
            for row in batch:
                v=c.visible(row);vis.append(v)
                prompts.append(tok.apply_chat_template([dict(role='system',content=c.PROMPT),dict(role='user',content=json.dumps(v,ensure_ascii=False,separators=(',',':')))],tokenize=False,add_generation_prompt=True,enable_thinking=False))
            enc=tok(prompts,return_tensors='pt',padding=True,add_special_tokens=False).to('cuda')
            funcs=[build_transformers_prefix_allowed_tokens_fn(td,JsonSchemaParser(SCHEMA)) for _ in batch]
            def prefix(i,ids):return funcs[i](i,ids)
            torch.cuda.synchronize();t=time.monotonic()
            with torch.inference_mode():
                output=model.generate(**enc,do_sample=False,max_new_tokens=CAP,pad_token_id=tok.pad_token_id,eos_token_id=tok.eos_token_id,prefix_allowed_tokens_fn=prefix,stopping_criteria=StoppingCriteriaList([Deadline()]),use_cache=True)
            torch.cuda.synchronize();seconds=time.monotonic()-t
            for i,row in enumerate(batch):
                ids=output[i,enc['input_ids'].shape[1]:].tolist()
                stopped=tok.eos_token_id in ids
                if stopped:ids=ids[:ids.index(tok.eos_token_id)]
                raw=tok.decode(ids,skip_special_tokens=True)
                if row.get('role','user')!='user':
                    # Guard is authenticated-role routing, with raw model output retained.
                    parsed=parse('[]',row,'stop');guard=True
                else:parsed=parse(raw,row,'stop' if stopped else 'length');guard=False
                rec=dict(id=row['id'],input=row,visible=vis[i],raw=raw,parsed=parsed,role_guard=guard,seconds=seconds,batch_size=len(batch),input_tokens=int(enc['attention_mask'][i].sum()),output_tokens=len(ids),finish_reason='stop' if stopped else 'length',request_sha256=c.digest(prompts[i]),usage=dict(prompt_tokens=int(enc['attention_mask'][i].sum()),completion_tokens=len(ids)))
                f.write(json.dumps(rec,ensure_ascii=False)+'\n');f.flush();records.append(rec)
            log(dict(stage=name,done=len(records),total=len(rows),seconds=round(time.monotonic()-start,2)))
    return records,time.monotonic()-start

def raw_dev(rec):
    row=dict(rec['raw']);row['id']=rec['id'];row['expected_ops']=rec['output'];return row

def setup_rows():
    bank=json.loads((R/'results/quick-checks/focus3-gate/v4/bank.json').read_text());out=[]
    for ei,ep in enumerate(bank['setup']):
        prev=''
        for ti,t in enumerate(ep['turns']):
            spans=[]
            for event in t['events']:
                if event['label'] in ['admit','supersedes']:
                    sp=c.span(t['text'],event['span']);sp.update(scope=event['scope'],key=event.get('gold_key',f"order:{event['scope']}"),event=event['label']);spans.append(sp)
            out.append(dict(id=f'setup:{ei}:{ti}',role='user',message=t['text'],previous_user=prev,standing_rules=spans,domain='v8-setup',one_off_request=True,quoted_or_reported=False));prev=t['text']
    assert len(out)==96
    return out

def acquire():
    import fcntl
    with (R/'.review.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        flags=list((R/'results/quick-checks').glob('**/RUNNING.flag'))
        if flags:raise RuntimeError('Other Stencil flag: '+str(flags))
        gpu=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader'],text=True)
        other=[l for l in gpu.splitlines() if l.strip() and not l.startswith('2705,') and 'llama-server' not in l]
        if other:raise RuntimeError('Other GPU process:'+str(other))
        with (P/'RUNNING.flag').open('x') as f:f.write(json.dumps(dict(pid=os.getpid(),started=time.time(),check=48)))
    with (R/'.stencil-owned-pids').open('a') as f:f.write(str(os.getpid())+'\n')

def main():
    import torch
    import peft
    from transformers import AutoTokenizer,AutoModelForCausalLM,set_seed
    from grammar import build_token_enforcer_tokenizer_data
    torch.set_num_threads(8);set_seed(0)
    # CPU setup, frozen inputs and grammar tokenizer prepared before occupancy.
    for path,d in json.loads((P/'freeze.json').read_text())['sha256'].items():assert c.sha(R/path)==d,path
    fit=c.rows(P/'fit-transitions.jsonl');dev=c.rows(P/'dev-transitions.jsonl');assert len(fit)==2048 and len(dev)==128
    tok=AutoTokenizer.from_pretrained(MODEL,local_files_only=True);tok.padding_side='left';tok.pad_token_id=tok.eos_token_id
    td=build_token_enforcer_tokenizer_data(tok)
    total_eval=sum(p.read_bytes().count(b'\n') for p in HELD)+96+128 # Header-inclusive conservative count only.
    acquire();start=time.monotonic();cost={'start_unix':time.time(),'reading':'INCOMPLETE','stage':'load','evaluation_rows_upper_bound':total_eval};model=None;optimizer=None
    try:
        loadstart=time.monotonic()
        model=AutoModelForCausalLM.from_pretrained(MODEL,dtype=torch.bfloat16,attn_implementation='sdpa',local_files_only=True).to('cuda')
        model=peft.get_peft_model(model,peft.LoraConfig(r=16,lora_alpha=32,target_modules=MODULES,lora_dropout=0,bias='none',task_type='CAUSAL_LM'))
        trainable=[p for p in model.parameters() if p.requires_grad]
        assert trainable and all('lora_' in n for n,p in model.named_parameters() if p.requires_grad)
        model.config.use_cache=False
        init={n:p.detach().cpu().clone() for n,p in model.named_parameters() if p.requires_grad}
        # Non-vacuous forward/backward smoke; no optimizer update retained.
        model.train();smoke=model(**batch_tensors(tok,fit[:BATCH]));smoke.loss.backward()
        assert torch.isfinite(smoke.loss)
        assert any(p.grad is not None and bool(p.grad.abs().sum()>0) for p in trainable)
        model.zero_grad(set_to_none=True);del smoke
        torch.cuda.synchronize();cost['load_smoke_seconds']=time.monotonic()-loadstart;check(loadstart+300)
        log(dict(stage='load_complete',seconds=cost['load_smoke_seconds'],trainable=sum(p.numel() for p in trainable)))
        cost['stage']='pilot';pilotstart=time.monotonic();deadline=pilotstart+300
        optimizer=torch.optim.AdamW(trainable,lr=1e-4,weight_decay=0,betas=(.9,.999),eps=1e-8)
        durations=[];tokens=0
        for j in range(6):
            check(deadline,30);t=time.monotonic();batch=fit[j*BATCH:(j+1)*BATCH];inp=batch_tensors(tok,batch)
            loss=model(**inp).loss;loss.backward();torch.nn.utils.clip_grad_norm_(trainable,1.0);optimizer.step();optimizer.zero_grad(set_to_none=True)
            torch.cuda.synchronize();durations.append(time.monotonic()-t);tokens+=int(inp['attention_mask'].sum());del loss,inp
            log(dict(stage='train_pilot',step=j+1,seconds=durations[-1]))
        train_projection=1.25*sum(durations[1:])/5*math.ceil(len(fit)/BATCH)+30
        # Reset every LoRA tensor, optimizer state and RNG before inference pilot/fixed fit.
        with torch.no_grad():
            for n,p in model.named_parameters():
                if p.requires_grad:p.copy_(init[n].to(p.device))
        del optimizer;optimizer=None;model.eval();model.config.use_cache=True;set_seed(0)
        pilotrows=[raw_dev(r) for r in sorted(dev,key=lambda r:(-r['output_tokens'],r['id']))[:8]]
        prec,pwall=infer(model,tok,td,pilotrows,'pilot-dev',deadline)
        eval_projection=1.25*pwall/len(prec)*total_eval
        cost.update(pilot_seconds=time.monotonic()-pilotstart,train_pilot_seconds=durations,train_tokens_per_second=tokens/sum(durations),projected_fit_save_seconds=train_projection,projected_evaluation_seconds=eval_projection,peak_memory_bytes=torch.cuda.max_memory_allocated(),pilot_can_fit=train_projection<=1500 and eval_projection<=1320)
        c.write('profile.json',cost);log(cost);check(deadline)
        if not cost['pilot_can_fit']:
            cost['reading']='COST-INELIGIBLE';return
        cost['stage']='fit';fitstart=time.monotonic();deadline=min(fitstart+1500,start+3420)
        model.train();model.config.use_cache=False;optimizer=torch.optim.AdamW(trainable,lr=1e-4,weight_decay=0,betas=(.9,.999),eps=1e-8)
        trained=0
        with (P/'training-records.jsonl').open('x') as f:
            for offset in range(0,len(fit),BATCH):
                check(deadline,max(durations)*1.5+15);t=time.monotonic();loss=model(**batch_tensors(tok,fit[offset:offset+BATCH])).loss
                if not torch.isfinite(loss):raise RuntimeError('nonfinite loss')
                loss.backward();torch.nn.utils.clip_grad_norm_(trainable,1.0);optimizer.step();optimizer.zero_grad(set_to_none=True);trained+=len(fit[offset:offset+BATCH]);torch.cuda.synchronize()
                rec=dict(step=offset//BATCH,trained=trained,loss=float(loss),seconds=time.monotonic()-t,ids=[r['id'] for r in fit[offset:offset+BATCH]])
                f.write(json.dumps(rec)+'\n');f.flush();del loss
                if trained%64==0:log(dict(stage='fit',trained=trained,seconds=time.monotonic()-fitstart))
        assert trained==2048;ADAPTER.mkdir(parents=True,exist_ok=False);model.save_pretrained(ADAPTER);tok.save_pretrained(ADAPTER)
        adapterhash={str(p.relative_to(R)):c.sha(p) for p in ADAPTER.iterdir() if p.is_file()}
        c.write('adapter-manifest.json',dict(sha256=adapterhash,trained=trained,epochs=1,seed=0,peft=peft.__version__,modules=MODULES,trainable=sum(p.numel() for p in trainable),base_sha256=json.loads((P/'freeze.json').read_text())['base_sha256']))
        check(deadline);cost['fit_save_seconds']=time.monotonic()-fitstart
        # Freeze the sole full-epoch adapter before any screening contents/model look.
        subprocess.run(['git','add','-f','--',str(P/'adapter-manifest.json'),str(P/'training-records.jsonl'),str(P/'profile.json')],cwd=R,check=True)
        subprocess.run(['git','commit','-m','check48: freeze single-epoch updater adapter before screening','--',str(P/'adapter-manifest.json'),str(P/'training-records.jsonl'),str(P/'profile.json')],cwd=R,check=True)
        del optimizer;optimizer=None;model.eval();model.config.use_cache=True
        cost['stage']='evaluation';evstart=time.monotonic();deadline=min(evstart+1320,start+3420)
        assert not (P/'evaluation-opened.json').exists();c.write('evaluation-opened.json',dict(time=time.time(),adapter_sha256=adapterhash))
        banks=[c.rows(p) for p in HELD]
        for name,bank in zip(['admission','relations'],banks):
            for i,row in enumerate(bank):row.setdefault('id',f'{name}:{i}');row.setdefault('message',row.get('new_message',''))
        for name,bank in [('dev',[raw_dev(r) for r in dev]),('admission',banks[0]),('relations',banks[1]),('setup',setup_rows())]:
            infer(model,tok,td,bank,name,deadline)
        cost['evaluation_seconds']=time.monotonic()-evstart;cost['reading']='COMPLETE_PENDING_SCORING';cost['stage']='complete'
    except BudgetStop as exc:
        cost['reading']='COST-INELIGIBLE' if cost['stage'] in ['load','pilot'] else 'INCOMPLETE';cost['reason']=str(exc)
    except Exception as exc:
        import traceback
        cost['error']=repr(exc);cost['traceback']=traceback.format_exc();log(cost)
    finally:
        cleanstart=time.monotonic()
        optimizer=None;model=None;gc.collect();torch.cuda.empty_cache();torch.cuda.synchronize()
        cost['cleanup_seconds']=time.monotonic()-cleanstart;cost['gpu_seconds']=time.monotonic()-start;c.write('cost.json',cost)
        (P/'RUNNING.flag').unlink();log(cost)

if __name__=='__main__':main()
