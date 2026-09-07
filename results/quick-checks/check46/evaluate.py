"""One-look loader and fixed scoring. Frozen before evaluation reads."""
import copy,json,sys,time
from collections import Counter
from pathlib import Path
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P))
import run as m
R=m.R

def admission_record(rec):
 a=copy.deepcopy(rec['parsed']);a['accepted']=[x for x in a['accepted'] if x['op']=='add'];a['seconds']=rec['seconds'];a['score']=m.metrics.score(a['accepted'],rec['input'])
 return dict(input=rec['input'],trunk=a)

def relation_score(rec):
 row=rec['input'];target=row['target_span']
 if isinstance(target,str):
  start=row['message'].index(target);target=dict(start=start,end=start+len(target),text=target)
 offset_repaired=False
 if row['message'][target['start']:target['end']]!=target['text']:
  pos=m.metrics.unique_span(row['message'],target['text']);assert pos, 'Gold quote must uniquely locate'
  target=dict(target,start=pos[0],end=pos[1]);offset_repaired=True
 ops=[x for x in rec['parsed']['accepted'] if x['op']!='add' and min(x['end'],target['end'])>max(x['start'],target['start'])]
 pred=ops[0]['op'] if len(ops)==1 else ('none' if not ops else 'ERROR_multiple')
 if rec['parsed']['failure'] or rec['parsed']['rejected']:pred='ERROR_invalid'
 return dict(gold_offset_repaired=offset_repaired,gold=row['label'],pred=pred,correct=pred==row['label'],target_correct=bool(ops) and all(x['target_id']=='r1' for x in ops),target_positive=row['label']!='none',overlapping_ops=len(ops))

def relation_summary(records):
 scores=[relation_score(r) for r in records];labels=['none','supersedes','cancels','completes','reinstates'];out={}
 for label in labels:
  tp=sum(s['gold']==s['pred']==label for s in scores);ng=sum(s['gold']==label for s in scores);np=sum(s['pred']==label for s in scores)
  p=tp/np if np else 0;r=tp/ng if ng else 0
  out[label]=dict(tp=tp,gold=ng,predicted=np,precision=p,recall=r,f1=2*p*r/(p+r) if p+r else 0)
 return dict(gold_offsets_repaired=sum(s['gold_offset_repaired'] for s in scores),n=len(scores),correct=sum(s['correct'] for s in scores),accuracy=sum(s['correct'] for s in scores)/len(scores),labels=out,confusion=dict(Counter(s['gold']+' -> '+s['pred'] for s in scores)),target_identification_positive=dict(correct=sum(s['target_correct'] and s['target_positive'] for s in scores),n=sum(s['target_positive'] for s in scores)),go=sum(s['correct'] for s in scores)/len(scores)>=.94 and out['supersedes']['recall']>=.85)

def setup_rows():
 # Exactly the inherited44b/c diagnostic, with one bank read and event metadata.
 bank=json.loads((R/'results/quick-checks/focus3-gate/v4/bank.json').read_text()); rows=[]
 for ei,ep in enumerate(bank['setup']):
  prev=''
  for ti,t in enumerate(ep['turns']):
   rules=[]
   for event in t['events']:
    if event['label'] in ['admit','supersedes']:
     span=m.metrics.unique_span(t['text'],event['span']);assert span
     rules.append(dict(text=event['span'],start=span[0],end=span[1],scope=event['scope'],key=event.get('gold_key',f"order:{event['scope']}"),event=event['label']))
   rows.append(dict(id=f'setup:{ei}:{ti}',role='user',message=t['text'],previous_user=prev,standing_rules=rules,domain='v8-setup',one_off_request=True,quoted_or_reported=False));prev=t['text']
 assert len(rows)==96
 return rows

def summarize():
 out={};all_records=[]
 for name in ['admission','relations','setup']:
  records=m.readrows(P/(name+'-records.jsonl'));all_records.extend(records)
  if name=='relations':out[name]=relation_summary(records);continue
  scored=[admission_record(r) for r in records];out[name]=m.metrics.aggregate(scored,'trunk')
  if name=='admission':
   o=out[name];o['go']=bool(o['go'] and o['overlap']['precision'] is not None and o['overlap']['precision']>=.95)
  else:
   o=out[name];o['false_admission_turns']=m.metrics.rate(sum(r['trunk']['score']['overlap']['fp']>0 for r in scored),len(scored));counts=Counter();recovered=Counter()
   for r in scored:
    g=r['input']['standing_rules'];counts.update(s['event'] for s in g)
    recovered.update(g[j]['event'] for _,j in r['trunk']['score']['overlap']['pairs'])
   o['events']={k:dict(recovered=recovered[k],n=counts[k]) for k in counts}
   o['go']=o['false_admission_turns']['errors']<=2 and o['events']['admit']==dict(recovered=36,n=36)
 failures=Counter(r['parsed']['failure'] for r in all_records if r['parsed']['failure'])
 out['failures']=dict(failures);out['span_rates']=dict(sum((Counter(r['parsed']['span_rates']) for r in all_records),Counter()))
 out['latency_seconds']=m.metrics.percentiles([r['seconds'] for r in all_records]);out['usage']=dict(sum((Counter({k:v for k,v in (r['usage'] or {}).items() if isinstance(v,int)}) for r in all_records),Counter()))
 a=out['admission']['go'];r=out['relations']['go'];s=out['setup']['go']
 complete=[out[k].get('messages',out[k].get('n')) for k in ['admission','relations','setup']]==[357,448,96]
 out['reading']='INCOMPLETE' if not complete else ('GO' if a and r and s else ('PARTIAL' if a!=r else 'NO-GO'))
 out['automation']={'admission':a and s,'relations':r};out['complete']=complete
 m.write('summary.json',out)
 return out

def evaluate():
 freeze=json.loads((P/'freeze.json').read_text())
 for path,digest in freeze['sha256'].items():assert m.sha(R/path)==digest,path
 profile=json.loads((P/'profile.json').read_text());assert profile['can_fit'] and profile['failures']==0
 assert not (P/'evaluation-opened.json').exists()
 m.write('evaluation-opened.json',dict(time=time.time(),freeze=freeze))
 # The only source reads for the two held-outs in this check. All replay uses records.
 a=m.readrows(R/'data/classifier/heldout/fable-admission-heldout-3.jsonl')
 r=m.readrows(R/'data/classifier/heldout/fable-relations-heldout-3.jsonl')
 s=setup_rows()
 assert len(a)==357 and len(r)==448
 assert sum(len(x['standing_rules']) for x in a)==385
 for name,rows in [('admission',a),('relations',r),('setup',s)]:
  for i,row in enumerate(rows):
   row.setdefault('id',name+':'+str(i))
   if 'message' not in row:row['message']=row['new_message']
  m.write(name+'-input-manifest.json',dict(n=len(rows),input_sha256=__import__('hashlib').sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()))
  records,wall=m.run_rows(rows,name+'-records')
  m.write(name+'-timing.json',dict(wall_seconds=wall,n=len(records)))
  if len(records)!=len(rows):break
 print(json.dumps(summarize(),indent=2))

if __name__=='__main__':
 if sys.argv[1]=='evaluate':evaluate()
 elif sys.argv[1]=='summarize':print(json.dumps(summarize(),indent=2))
