"""Frozen check46 inference. No reads/inference occur on import."""
import concurrent.futures as cf
import copy, hashlib, json, re, statistics, subprocess, sys, time, urllib.request
from pathlib import Path
P=Path(__file__).resolve().parent
R=P.parents[2]
sys.path.insert(0,str(R))
from scripts import focus_check44 as metrics

def write(name,obj):
 (P/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n')
def readrows(path):
 return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def normalize(s):
 out=[]; offsets=[]
 for i,c in enumerate(s):
  c={'“':'"','”':'"','‘':"'",'’':"'"}.get(c,c)
  if c.isspace():
   if out and out[-1]==' ': offsets[-1][1]=i+1; continue
   c=' '
  for x in c.casefold():out.append(x);offsets.append([i,i+1])
 return ''.join(out),offsets

def locate(message,span):
 if not span.strip():return None,'empty_span'
 i=message.find(span)
 if i>=0:
  if message.find(span,i+1)>=0:return None,'ambiguous_raw_span'
  return (i,i+len(span)),'raw'
 m,mp=normalize(message);s,_=normalize(span); s=s.strip()
 i=m.find(s)
 if i<0:return None,'non_verbatim'
 if m.find(s,i+1)>=0:return None,'ambiguous_normalized_span'
 return (mp[i][0],mp[i+len(s)-1][1]),'normalized'

def grammar(message):
 # Shared suffix productions accept every nonempty contiguous character substring.
 # JSON-escape each source character, then quote it as an EBNF terminal.
 q=lambda s:json.dumps(s,ensure_ascii=False)
 literal=lambda s:q(json.dumps(s,ensure_ascii=False))
 g=['root ::= "[" ws (item (ws "," ws item)*)? ws "]"',
    'ws ::= [ \\n\\t\\r]*',
    r'str ::= "\"" ([^"\\\x00-\x1f] | "\\" (["\\/bfnrt] | "u" [0-9a-fA-F]{4}))* "\""',
    'op ::= '+ ' | '.join(literal(x) for x in ['add','supersedes','cancels','completes','reinstates','none']),
    'target ::= str | "null"',
    'span ::= '+q('"')+' ('+' | '.join('s'+str(i) for i in range(len(message)))+') '+q('"')]
 fields=[('op','op'),('span','span'),('key','str'),('scope','str'),('kind','str'),('value','str'),('target_id','target')]
 g.append('item ::= "{" ws '+' ws "," ws '.join(literal(k)+' ws ":" ws '+v for k,v in fields)+' ws "}"')
 for i,c in enumerate(message):
  encoded=json.dumps(c,ensure_ascii=False)[1:-1]
  g.append('s%d ::= %s%s'%(i,q(encoded),(' s%d?'%(i+1)) if i+1<len(message) else ''))
 return '\n'.join(g)

def visible(row):
 old=row.get('old_rule')
 register=[]
 if old:
  if isinstance(old,dict):
   d=old
  else:d=dict(text=old,key=row.get('key',''),scope=row.get('scope',''),status=row.get('status','live'))
  register=[dict(id='r1',key=d.get('key',''),scope=d.get('scope',''),kind=d.get('kind',''),value=d.get('value',''),text=d['text'],version=d.get('version',1),status=d.get('status','live'))]
 prev=row.get('prev_user') or row.get('previous_user') or ''
 if isinstance(prev,list):prev=' '.join(prev)
 prev=re.split(r'(?<=[.!?])\s+',prev)[-2:] if prev else []
 return dict(register=register,role=row.get('role','user'),message=row.get('message',row.get('new_message','')),previous_user=prev)

def request(row):
 v=visible(row)
 messages=[dict(role='system',content=(P/'prompt.txt').read_text())]
 for e in json.loads((P/'few-shot.json').read_text()):
  messages.extend([dict(role='user',content=json.dumps(e['input'],ensure_ascii=False)),dict(role='assistant',content=json.dumps(e['output'],ensure_ascii=False))])
 messages.append(dict(role='user',content=json.dumps(v,ensure_ascii=False)))
 return dict(model='/model',messages=messages,temperature=0,top_p=1,top_k=-1,min_p=0,repetition_penalty=1,frequency_penalty=0,presence_penalty=0,max_tokens=512,seed=0,stop_token_ids=[151645,151643],ignore_eos=False,chat_template_kwargs={'enable_thinking':False},structured_outputs={'grammar':grammar(v['message'])})

def parse(raw,row,finish):
 result=dict(accepted=[],rejected=[],span_rates=dict(proposed=0,raw=0,normalized_only=0,normalized_inclusive=0),failure=None)
 if finish!='stop':result['failure']='truncated' if finish=='length' else 'finish_'+str(finish);return result
 try:
  ops=json.loads(raw)
  schema=json.loads((P/'schema.json').read_text())['items']
  assert isinstance(ops,list)
  for op in ops:
   assert isinstance(op,dict) and set(op)==set(schema['required'])
   assert all(isinstance(op[k],str) for k in schema['required'] if k!='target_id')
   assert op['target_id'] is None or isinstance(op['target_id'],str)
   assert op['op'] in schema['properties']['op']['enum']
 except Exception as e:result['failure']='json_or_schema';result['detail']=str(e)[:500];return result
 for op in ops:
  result['span_rates']['proposed']+=1
  span,cat=locate(visible(row)['message'],op['span'])
  if cat=='raw':result['span_rates']['raw']+=1
  if cat=='normalized':result['span_rates']['normalized_only']+=1
  if span:result['span_rates']['normalized_inclusive']+=1
  reason=None
  if not span:reason=cat
  elif op['op'] not in ['add','none'] and op['target_id']!='r1':reason='invalid_target'
  elif op['op'] not in ['add','none'] and not row.get('old_rule'):reason='missing_register_target'
  elif op['op']=='add' and op['target_id'] is not None:reason='add_has_target'
  if reason:result['rejected'].append(dict(op=op,reason=reason));continue
  if op['op']!='none':result['accepted'].append(dict(op,start=span[0],end=span[1],match=cat,allocated_key=op['key']))
 return result

def call(row):
 start=time.time();body=request(row)
 record=dict(id=row['id'],input=row,visible=visible(row),request_sha256=hashlib.sha256(json.dumps(body,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),started=start)
 try:
  req=urllib.request.Request('http://127.0.0.1:18081/v1/chat/completions',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
  with urllib.request.urlopen(req,timeout=150) as r:response=json.load(r)
  choice=response['choices'][0];raw=choice['message']['content'] or ''
  record.update(raw=raw,finish_reason=choice['finish_reason'],usage=response.get('usage'),parsed=parse(raw,row,choice['finish_reason']))
 except Exception as e:
  detail=e.read().decode() if hasattr(e,'read') else str(e)
  record.update(raw='',usage=None,parsed=dict(accepted=[],rejected=[],span_rates={},failure='http_error',detail=detail))
 record['seconds']=time.time()-start
 return record

def run_rows(rows,name):
 path=P/(name+'.jsonl');assert not path.exists(), 'No repeated evaluations'
 records=[];start=time.time()
 with path.open('x') as f,cf.ThreadPoolExecutor(max_workers=4) as pool:
  for offset in range(0,len(rows),4):
   server=json.loads((P/'server.json').read_text())
   if time.time()-server['start']>3420:break
   futures=[pool.submit(call,r) for r in rows[offset:offset+4]]
   for future in futures:
    rec=future.result();f.write(json.dumps(rec,ensure_ascii=False)+'\n');f.flush();records.append(rec)
   print(json.dumps(dict(bank=name,done=len(records),total=len(rows),elapsed=round(time.time()-start,2),failures=sum(bool(x['parsed']['failure']) for x in records))),flush=True)
 return records,time.time()-start

def dev():
 rows=[]
 # Spread deterministically across source order; 10 admission +10 relations.
 for name in ['kimi-admission-2.jsonl','kimi-overrides.jsonl']:
  source=readrows(R/'data/classifier/relations'/name)
  for i in [j*(len(source)-1)//9 for j in range(10)]:
   row=copy.deepcopy(source[i]);row['id']='dev:'+name+':'+str(i);rows.append(row)
 records,wall=run_rows(rows,'dev-records')
 elapsed=time.time()-json.loads((P/'server.json').read_text())['start']
 projection=elapsed+1.25*wall/20*901+120
 out=dict(n=len(records),wall_seconds=wall,elapsed_gpu_seconds=elapsed,projected_total_seconds=projection,latency=metrics.percentiles([x['seconds'] for x in records]),failures=sum(bool(x['parsed']['failure']) for x in records),can_fit=projection<=3600)
 write('profile.json',out); print(json.dumps(out,indent=2))

if __name__=='__main__':
 if sys.argv[1]=='dev':dev()
