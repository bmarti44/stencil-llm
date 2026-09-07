"""Cache-matched teacher-forced parity audit; no generation, fit, or selection.

Resolves full-sequence vs incremental floating-point-path mismatch. All inputs
and forced output tokens come from the sixteen registered baseline records.
The frozen experiment's original parity.json and verdict remain unchanged.
"""
import contextlib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import time

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'results/quick-checks/check49'


def main():
    import torch
    from transformers import AutoModelForCausalLM, DynamicCache
    from peft import PeftModel
    spec=importlib.util.spec_from_file_location('check49',ROOT/'scripts/focus_check49.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    assert not (OUT/'cached-parity.json').exists()
    summary=json.loads((OUT/'summary.json').read_text())
    assert summary['gpu_held_seconds']+360<3600
    assert not list((ROOT/'results/quick-checks').glob('*/RUNNING.flag'))
    flag=OUT/'RUNNING.flag'
    with flag.open('x') as f: f.write(json.dumps(dict(pid=os.getpid(),purpose='registered16 cache-matched tensor audit')))
    with (ROOT/'.stencil-owned-pids').open('a') as f: f.write(str(os.getpid())+'\n')
    started=time.monotonic()
    report=dict(status='INCOMPLETE',rows=[])
    model=None
    try:
        torch.set_num_threads(8)
        torch.manual_seed(0)
        torch.backends.cuda.matmul.allow_tf32=False
        torch.backends.cudnn.allow_tf32=False
        torch.use_deterministic_algorithms(True)
        base=AutoModelForCausalLM.from_pretrained(m.BASE,local_files_only=True,dtype=torch.bfloat16,attn_implementation='sdpa').to('cuda')
        model=PeftModel.from_pretrained(base,m.ADAPTERS/'python',adapter_name='python',autocast_adapter_dtype=False)
        model.load_adapter(m.ADAPTERS/'js',adapter_name='js',autocast_adapter_dtype=False)
        model.eval()
        for p,h in json.loads((OUT/'adapter-manifest.json').read_text()).items():
            assert m.sha(ROOT/p)==h['sha256']
        rows=[json.loads(x) for x in (OUT/'records.jsonl').read_text().splitlines()]
        rows=[r for r in rows if r['id'].startswith('baseline/python/') or r['id'].startswith('baseline/None/')]
        assert len(rows)==16
        def replay(r,bypass):
            ids=torch.tensor([r['input_ids']],device='cuda')
            kwargs=dict(attention_mask=torch.ones_like(ids),past_key_values=DynamicCache(config=base.config),use_cache=True,logits_to_keep=1)
            h=hashlib.sha256();pred=[]; mismatches=[]
            with model.disable_adapter(),m.pristine(model) if bypass else contextlib.nullcontext(),torch.inference_mode(),base._optimize_model_for_decode():
                for i,token in enumerate(r['token_ids']):
                    if time.monotonic()-started>300:
                        raise RuntimeError('cooperative audit ceiling300s +cleanup60s')
                    inputs=base.prepare_inputs_for_generation(ids,next_sequence_length=None if i==0 else 1,is_first_iteration=i==0,**kwargs)
                    out=base(**inputs,return_dict=True)
                    logits=out.logits[:,-1,:]
                    h.update(logits.contiguous().view(torch.uint8).cpu().numpy().tobytes())
                    prediction=int(logits.argmax(-1))
                    pred.append(prediction)
                    if prediction!=token: mismatches.append(dict(position=i,saved=token,predicted=prediction))
                    kwargs=base._update_model_kwargs_for_generation(out,kwargs,is_encoder_decoder=False)
                    # Replay the SAVED token, regardless of argmax. No new generation.
                    ids=torch.cat([ids,torch.tensor([[token]],device='cuda')],dim=-1)
            return dict(logits_sha256=h.hexdigest(),predicted_tokens=pred,saved_token_mismatches=mismatches)
        for r in rows:
            off=replay(r,False);pristine=replay(r,True)
            row=dict(id=r['id'],off=off,pristine=pristine,logits_equal=off['logits_sha256']==pristine['logits_sha256'],token_equal=off['predicted_tokens']==pristine['predicted_tokens'],matches_saved=not off['saved_token_mismatches'] and not pristine['saved_token_mismatches'])
            report['rows'].append(row)
            print(json.dumps({k:v for k,v in row.items() if k not in ['off','pristine']}),flush=True)
        report.update(status='COMPLETE',off_pristine_logit_diffs=sum(not r['logits_equal'] for r in report['rows']),off_pristine_token_diffs=sum(not r['token_equal'] for r in report['rows']),saved_greedy_sequence_diffs=sum(not r['matches_saved'] for r in report['rows']))
    except Exception as e:
        import traceback
        report.update(error=repr(e),traceback=traceback.format_exc())
        print(report['traceback'],flush=True)
    finally:
        if model is not None:
            model.base_model.disable_adapter_layers()
            model.cpu()
        model=None
        if 'base' in locals(): del base
        import gc
        gc.collect();torch.cuda.empty_cache();torch.cuda.synchronize()
        report['gpu_held_seconds']=time.monotonic()-started
        report['combined_gpu_held_seconds']=summary['gpu_held_seconds']+report['gpu_held_seconds']
        report['generation_calls']=0
        m.write(OUT/'cached-parity.json',report)
        flag.unlink()
        print(json.dumps({k:v for k,v in report.items() if k!='rows'}),flush=True)


if __name__=='__main__': main()
