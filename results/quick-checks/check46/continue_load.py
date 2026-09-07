"""Header-only loader correction after count assertion; frozen science unchanged."""
import json,sys,time
from pathlib import Path
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P))
import run as m, evaluate as e

def main():
 freeze=json.loads((P/'freeze.json').read_text())
 for path,digest in freeze['sha256'].items():assert m.sha(m.R/path)==digest,path
 a=[x for x in json.loads((P/'admission-source-snapshot.json').read_text()) if 'summary' not in x]
 r=[x for x in json.loads((P/'relations-source-snapshot.json').read_text()) if 'summary' not in x]
 s=e.setup_rows()
 assert len(a)==357 and len(r)==448 and sum(len(x['standing_rules']) for x in a)==385
 for name,rows in [('admission',a),('relations',r),('setup',s)]:
  for i,row in enumerate(rows):row.setdefault('id',name+':'+str(i))
  records,wall=m.run_rows(rows,name+'-records')
  m.write(name+'-timing.json',dict(wall_seconds=wall,n=len(records)))
  if len(records)!=len(rows):return
 print(json.dumps(e.summarize(),indent=2))
if __name__=='__main__':main()
