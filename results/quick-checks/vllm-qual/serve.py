"""Bounded, owned-container startup and cleanup; no host process signals."""
import json, subprocess, time, urllib.request
from pathlib import Path
ROOT = Path('/home/bmarti44/stencil-llm')
OUT = ROOT / 'results/quick-checks/vllm-qual'
IMAGE = 'vllm/vllm-openai@sha256:3dbe092ec5b2cef63b6104d33fa75d6ce53a7870962529ada69f78bbbc38e776'
def cmd(args):
    return subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
def main():
    others = [p for p in (ROOT/'results/quick-checks').glob('*/RUNNING.flag') if p.parent != OUT]
    if others: raise RuntimeError(f'Other GPU flags: {others}')
    start = time.time()
    (OUT/'RUNNING.flag').write_text(json.dumps({'start':start,'owner':'vllm-qual','deadline':start+2670}))
    attempts=[]
    try:
        for i,(util,length) in enumerate([('0.70','32768'),('0.60','16384')]):
            name=f'stencil-vllm-qual-{int(start)}-{i}'
            args=['docker','run','-d','--name',name,'--device','nvidia.com/gpu=0','--ipc=host','-p','127.0.0.1:18081:8000','-e','VLLM_BATCH_INVARIANT=1','-v',f'{ROOT}/models/qwen3-30b-a3b-hf:/model:ro',IMAGE,'--attention-backend','TRITON_ATTN','--model','/model','--dtype','bfloat16','--kv-cache-dtype','auto','--tensor-parallel-size','1','--max-model-len',length,'--max-num-seqs','4','--max-num-batched-tokens','2048','--gpu-memory-utilization',util,'--enable-prefix-caching','--generation-config','vllm']
            a={'attempt':i,'command':args,'started':time.time()};attempts.append(a)
            result=cmd(args);a['launch']=result.stdout;a['launch_code']=result.returncode
            (OUT/'attempts.json').write_text(json.dumps(attempts,indent=2))
            if result.returncode: break
            (OUT/'container.json').write_text(json.dumps({'name':name,'id':result.stdout.strip()}))
            try:
                ready=False
                while time.time()<start+2610:
                    status=cmd(['docker','inspect','--format','{{.State.Status}}',name]).stdout.strip()
                    (OUT/f'server-{i}.log').write_text(cmd(['docker','logs','--timestamps',name]).stdout)
                    if status!='running':a['terminal_status']=status;break
                    try:
                        with urllib.request.urlopen('http://127.0.0.1:18081/health',timeout=2) as r:
                            ready=r.status==200
                    except Exception: pass
                    if ready:
                        a['ready_at']=time.time();(OUT/'READY').write_text(name);break
                    time.sleep(3)
                if ready:
                    while time.time()<start+2610 and not (OUT/'DONE').exists():time.sleep(2)
                    a['completion']='client_done' if (OUT/'DONE').exists() else 'deadline'
                else:a['completion']='startup_failed'
            finally:
                a['stop']=cmd(['docker','stop','-t','20',name]).stdout
                (OUT/f'server-{i}.log').write_text(cmd(['docker','logs','--timestamps',name]).stdout)
                a['inspect']=json.loads(cmd(['docker','inspect',name]).stdout)
                a['remove']=cmd(['docker','rm',name]).stdout;a['ended']=time.time()
                (OUT/'attempts.json').write_text(json.dumps(attempts,indent=2))
                (OUT/'READY').unlink(missing_ok=True)
            if ready: break
            log=(OUT/f'server-{i}.log').read_text().lower()
            if not any(s in log for s in ['out of memory','memory profiling','free memory','kv cache','memory utilization']):break
            if time.time()>start+2400:break
    finally:
        (OUT/'lifecycle.json').write_text(json.dumps({'start':start,'end':time.time(),'gpu_held_seconds':time.time()-start},indent=2))
        (OUT/'RUNNING.flag').unlink(missing_ok=True)
if __name__=='__main__':main()
