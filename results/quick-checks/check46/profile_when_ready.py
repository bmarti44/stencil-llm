import json,subprocess,time,urllib.request
from pathlib import Path
P=Path(__file__).resolve().parent
start=json.loads((P/'server.json').read_text())['start']
while time.time()-start<1100:
 try:
  with urllib.request.urlopen('http://127.0.0.1:18081/health',timeout=3) as r:
   if r.status==200:break
 except Exception:time.sleep(10)
else:raise SystemExit('INCOMPLETE startup timeout')
(P/'ready.json').write_text(json.dumps({'ready':time.time(),'startup_seconds':time.time()-start}))
raise SystemExit(subprocess.call([str(P.parents[2]/'.venv/bin/python'),str(P/'run.py'),'dev'],cwd=P.parents[2]))
