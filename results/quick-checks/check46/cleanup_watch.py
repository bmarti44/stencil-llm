"""Stop only this check's recorded container on completion or hard budget deadline."""
import json,subprocess,time
from pathlib import Path
P=Path(__file__).resolve().parent
s=json.loads((P/'server.json').read_text())
assert s['name']=='stencil-check46' and len(s['id'])==64
while not (P/'summary.json').exists() and time.time()-s['start']<3560:time.sleep(5)
reason='completed' if (P/'summary.json').exists() else 'budget_deadline'
start=time.time()
logs=subprocess.run(['docker','logs',s['id']],capture_output=True,text=True)
(P/'server.log').write_text(logs.stdout+logs.stderr)
stop=subprocess.run(['docker','stop','--time','10',s['id']],capture_output=True,text=True)
rm=subprocess.run(['docker','rm',s['id']],capture_output=True,text=True)
result=dict(reason=reason,cleanup_seconds=time.time()-start,gpu_held_seconds=time.time()-s['start'],stop_returncode=stop.returncode,rm_returncode=rm.returncode,stop_stdout=stop.stdout,stop_stderr=stop.stderr,rm_stdout=rm.stdout,rm_stderr=rm.stderr)
(P/'cleanup.json').write_text(json.dumps(result,indent=2)+'\n')
if stop.returncode==rm.returncode==0:(P/'RUNNING.flag').unlink(missing_ok=True)
print(json.dumps(result),flush=True)
