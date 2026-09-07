"""Descriptive post-freeze families; no inference/selection. IDs retained for audit."""
import json,re,sys
from collections import Counter
from pathlib import Path
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P))
import run as m, evaluate as e
CUES=r'\b(always|never|every|each|whenever|throughout|henceforth|going forward|from (?:now|here|today|this)|until|for now|in future|continue)\b'

def summarize():
 a=m.readrows(P/'admission-records.jsonl');rs=m.readrows(P/'relations-records.jsonl')
 scored=[e.admission_record(r) for r in a];out={'definitions':{'cue_less':'Gold spans without the case-insensitive lexical CUES pattern; descriptive lexical proxy, not a manually validated linguistic category. Span-level, siblings do not receive credit.','CUES':CUES,'multi_single_sentence':'All gold spans in the same regex sentence (boundary [.!?] followed by whitespace/end); report author two_rules category separately.','relations':'Gold supersedes rows selected by author rationale idioms; these are recall subsets, not inference features.','withdraw_replace_regex':r'scrap-|not a bare|retirement|dropping-|scratch-|A-is-out|was-a-mistake|A-is-no-good'},'admission':{},'relations':{}}
 for cat in ['two_rules','rule_plus_payload','buried_rule','payload_request','inert_quote']:
  sub=[r for r in scored if r['input'].get('category')==cat]
  out['admission'][cat]=dict(n=len(sub),overlap=m.metrics.aggregate(sub,'trunk')['overlap'],ids=[r['input']['id'] for r in sub])
 for n in [2,3]:
  sub=[]
  for r in scored:
   gold=r['input']['standing_rules'];msg=r['input']['message'];breaks=[x.end() for x in re.finditer(r'[.!?](?:\s+|$)',msg)]
   sentence=lambda pos:sum(b<=pos for b in breaks)
   if len(gold)==n and len({sentence(g['start']) for g in gold})==1:sub.append(r)
  out['admission'][f'{n}_rules_single_sentence']=dict(n=len(sub),overlap=m.metrics.aggregate(sub,'trunk')['overlap'],ids=[r['input']['id'] for r in sub])
 cue_ids=[];denom=tp=0
 for r in scored:
  gold=r['input']['standing_rules'];indices={i for i,g in enumerate(gold) if not re.search(CUES,g['text'],re.I)}
  hits={j for _,j in r['trunk']['score']['overlap']['pairs']};denom+=len(indices);tp+=len(indices&hits)
  if indices:cue_ids.append(dict(id=r['input']['id'],gold_indices=sorted(indices),recovered_indices=sorted(indices&hits)))
 out['admission']['cue_less']=dict(spans=denom,recovered=tp,recall=tp/denom if denom else None,rows=cue_ids)
 predicates={
 'withdraw_replace':lambda r:re.search(out['definitions']['withdraw_replace_regex'],r['why'],re.I),
 'bare_value_temporal':lambda r:'bare new' in r['why'].lower(),
 'task_override_global':lambda r:'task-scoped' in r['why'].lower() and 'global' in r['why'].lower(),
 'actually_B':lambda r:'actually-b' in r['why'].lower()}
 for family,pred in predicates.items():
  sub=[r for r in rs if r['input']['label']=='supersedes' and pred(r['input'])];scores=[e.relation_score(r) for r in sub]
  out['relations'][family]=dict(n=len(sub),correct=sum(s['correct'] for s in scores),recall=sum(s['correct'] for s in scores)/len(scores) if scores else None,ids=[r['id'] for r in sub],miss_ids=[r['id'] for r,s in zip(sub,scores) if not s['correct']])
 m.write('families.json',out);return out
if __name__=='__main__':print(json.dumps(summarize(),indent=2))
