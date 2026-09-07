"""Replay only saved records; never reread evaluation banks."""
import hashlib,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P))
import run as m

def audit():
 count=0;banks={}
 for path in sorted(P.glob('*-records.jsonl')):
  records=m.readrows(path);ids=[]
  for rec in records:
   ids.append(rec['id']);count+=1
   assert rec['visible']==m.visible(rec['input'])
   request=m.request(rec['input'])
   digest=hashlib.sha256(json.dumps(request,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
   assert digest==rec['request_sha256']
   if rec['parsed']['failure']!='http_error':assert rec['parsed']==m.parse(rec['raw'],rec['input'],rec['finish_reason'])
   assert rec['seconds']>=0
  assert len(ids)==len(set(ids))
  banks[path.name]=len(records)
 oversized=[str(p) for p in P.iterdir() if p.is_file() and p.stat().st_size>10_000_000]
 assert not oversized
 result=dict(records=count,banks=banks,request_and_parse_replay='PASS',oversized=oversized)
 m.write('audit.json',result);print(json.dumps(result))
if __name__=='__main__':audit()
