import json,subprocess,time
from pathlib import Path

def main():
 P=Path(__file__).resolve().parent
 R=P.parents[2]
 flags=list((R/'results/quick-checks').glob('**/RUNNING.flag'))
 assert not flags, flags
 (P/'RUNNING.flag').write_text('check46 owned qualified vLLM; no other processes may be signalled\n')
 r=json.loads((R/'results/quick-checks/composition-pilot-4/registration.json').read_text())
 cmd=r['command']; cmd[cmd.index('--name')+1]='stencil-check46'
 state={'start':time.time(),'command':cmd,'name':'stencil-check46','cap_seconds':3600}
 (P/'server.json').write_text(json.dumps(state,indent=2))
 p=subprocess.run(cmd,capture_output=True,text=True)
 state.update(id=p.stdout.strip(),returncode=p.returncode,stderr=p.stderr)
 (P/'server.json').write_text(json.dumps(state,indent=2))
 print(json.dumps(state))
 if p.returncode: (P/'RUNNING.flag').unlink()

if __name__ == "__main__":
 main()
