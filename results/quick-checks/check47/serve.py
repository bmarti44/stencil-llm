"""Bounded check47 native then text-only load, owning only named containers."""
import json, subprocess, time, urllib.request
from pathlib import Path
ROOT=Path('/home/bmarti44/stencil-llm')
OUT=ROOT/'results/quick-checks/check47'
IMAGE='vllm/vllm-openai@sha256:3dbe092ec5b2cef63b6104d33fa75d6ce53a7870962529ada69f78bbbc38e776'
def cmd(a):
    r=subprocess.run(a,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    return {'code':r.returncode,'output':r.stdout}
def main():
    others=[str(p) for p in (ROOT/'results/quick-checks').rglob('RUNNING.flag') if p.parent!=OUT]
    if others: raise RuntimeError(others)
    gpu=cmd(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'])
    (OUT/'gpu-before.json').write_text(json.dumps(gpu,indent=2))
    if any('python' in l for l in gpu['output'].splitlines()):raise RuntimeError(gpu)
    start=time.time(); deadline=start+2400
    (OUT/'RUNNING.flag').write_text(json.dumps({'start':start,'deadline':deadline,'owner':'check47'}))
    attempts=[]
    try:
        for i in range(2):
            name=f'stencil-check47-{int(start)}-{i}'
            args=['docker','run','-d','--name',name,'--device','nvidia.com/gpu=0','--ipc=host','-p','127.0.0.1:18087:8000','-e','VLLM_BATCH_INVARIANT=1','-v','/home/bmarti44/models/qwen3.8-27b-fp8:/model:ro',IMAGE,'--model','/model','--dtype','bfloat16','--attention-backend','TRITON_ATTN','--kv-cache-dtype','auto','--tensor-parallel-size','1','--max-model-len','32768','--max-num-seqs','4','--max-num-batched-tokens','2048','--gpu-memory-utilization','0.65','--enable-prefix-caching','--generation-config','vllm']
            if i:args += ['--hf-overrides','{"language_model_only":true}','--language-model-only']
            a={'attempt':i,'text_only':bool(i),'command':args,'start':time.time()};attempts.append(a)
            a['launch']=cmd(args)
            (OUT/'attempts.json').write_text(json.dumps(attempts,indent=2))
            if a['launch']['code']:break
            try:
                ready=False
                while time.time()<deadline-30:
                    (OUT/f'server-{i}.log').write_text(cmd(['docker','logs','--timestamps',name])['output'])
                    if cmd(['docker','inspect','--format','{{.State.Status}}',name])['output'].strip()!='running':break
                    try:
                        with urllib.request.urlopen('http://127.0.0.1:18087/health',timeout=2) as r:ready=r.status==200
                    except Exception:pass
                    if ready:break
                    time.sleep(3)
                a['ready']=ready
                if ready:
                    a['ready_at']=time.time();(OUT/'READY').write_text(name)
                    while time.time()<deadline-30 and not (OUT/'DONE').exists():time.sleep(2)
            finally:
                a['stop']=cmd(['docker','stop','-t','10',name])
                (OUT/f'server-{i}.log').write_text(cmd(['docker','logs','--timestamps',name])['output'])
                a['inspect']=json.loads(cmd(['docker','inspect',name])['output'])
                a['remove']=cmd(['docker','rm',name]);a['end']=time.time()
                (OUT/'attempts.json').write_text(json.dumps(attempts,indent=2));(OUT/'READY').unlink(missing_ok=True)
            if ready or time.time()>deadline-30:break
    finally:
        (OUT/'lifecycle.json').write_text(json.dumps({'start':start,'end':time.time(),'gpu_held_seconds':time.time()-start,'cap_seconds':2400},indent=2))
        (OUT/'RUNNING.flag').unlink(missing_ok=True)
if __name__=='__main__':main()
