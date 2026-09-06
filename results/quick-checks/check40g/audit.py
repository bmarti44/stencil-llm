"""CPU-only record audit; no model load or sealed inputs."""
import sys,json,hashlib,copy
from pathlib import Path
from collections import Counter
ROOT=Path('/home/bmarti44/stencil-llm')
sys.path.insert(0,str(ROOT/'scripts'))
import focus_check40g as g
import torch
out=g.OUT
freeze=json.loads((out/'freeze.json').read_text())
assert all(g.base.sha(ROOT/p)==h for p,h in freeze.items())
rows=[json.loads(s) for s in (out/'records.jsonl').read_text().splitlines()]
bank=json.loads((out/'banks.json').read_text())
tasks={t['id']:t for pair in ('TS','P2','Go') for split in ('competence','screen') for t in bank[pair][split]}
tasks.update({t['id']:t for episode in bank['release'] for t in episode.values()})
summary=json.loads((out/'summary.json').read_text())
js=torch.load(out/'js-control-bias.pt',weights_only=True,map_location='cpu')
old=torch.load(g.e.OUT/'P1-profiles.pt',weights_only=True,map_location='cpu')['biases']
biases={'positive-control':{'correct':js},'TS-alpha4.5':{a:b*1.5 for a,b in old.items()},'TS-alpha6':{a:b*2 for a,b in old.items()}}
for name in ('TS-fence','P2','Go'):
 p=out/f'{name}-profiles.pt'
 if p.exists():biases[name if name=='TS-fence' else name+'-screen']=torch.load(p,weights_only=True,map_location='cpu')['biases']
scored=0
for j,r in enumerate(rows):
 assert r['id']==j
 t=dict(tasks[r['task_id']])
 if r['phase']=='positive-control':t['js_control']=True
 assert g.score(r['text'],t,r['truncated'])==r['score'],r['id']
 scored+=1
 d=r['dispatch']
 assert {int(k.split('-')[0]) for k in d}==set(range(48))
 for v in d.values():
  assert v['tokens']>0 and 0<=v['changed_route_tokens']<=v['tokens'] and v['consumer_mismatches']==0
  assert v['route_change_fraction']==v['changed_route_tokens']/v['tokens']
  if r['bias_sha256'] is None:assert v['changed_route_tokens']==v['changed_weight_tokens']==0
 bias=biases.get(r['phase'],{}).get(r['arm'])
 if r['phase']=='release':
  bs=dict(js=biases['Go-screen']['correct'],shuffled=biases['Go-screen']['shuffled'])
  bias=g.i.bias_for(r['arm'],r['step'],bs)
  bodies=[(len(q['cache_prefix_token_ids'])+len(q['input_token_ids']),len(q['cache_prefix_token_ids'])+len(q['input_token_ids'])+len(q['generated_token_ids'])-int(q['eos'])) for q in rows[:j] if q['phase']=='release' and q['episode']==r['episode'] and q['arm']==r['arm']]
  if r['step'] in ('SWITCH','BACK','CLEAR') and r['arm']!='OFF':
   assert r['mask_event']['bodies']==[list(b) for b in bodies]
   assert r['masked_positions']==sorted({p for b,e in bodies for p in range(b,e)})
  if r['arm']=='OFF':assert not r['masked_positions']
 digest=None if bias is None else hashlib.sha256(bias.float().numpy().tobytes()).hexdigest()
 assert digest==r['bias_sha256'],r['id']
actual=[r for r in rows if 'shared_from_generation' not in r]
assert summary['records']==len(rows) and summary['generations']==len(actual)
assert summary['generated_tokens']==sum(len(r['generated_token_ids']) for r in actual)
control=sum(r['score']['valid_skill']=='JavaScript' for r in actual if r['phase']=='positive-control')
assert summary['positive_control']['javascript']==control
if control<6: assert summary['reading']=='INVALID' and len(rows)==8
for pair,p in summary['pairs'].items():
 if 'arms' not in p:continue
 target='SQL' if pair=='P2' else 'Go' if pair=='Go' else 'TypeScript'
 phase=pair+'-screen' if pair in ('P2','Go') else pair
 arms=g.ARMS if pair in ('P2','Go') else ('OFF','correct','shuffled','text-cue')
 replay=g.screen_summary(rows,phase,target,p['n'],arms)
 assert all(p[k]==v for k,v in replay.items()),pair
if 'release' in summary:assert g.release_summary(rows,True)==summary['release']
assert summary['gpu_seconds']<=3600 and summary['cap_overrun_seconds']==0
assert not (out/'RUNNING.flag').exists()
report=dict(freeze_hashes=True,score_replays=scored,record_counts=True,all48_layer_dispatch_consumers=True,off_records_checked=sum(r["bias_sha256"] is None for r in actual),bias_digests=True,paired_decisions=True,release_decision_and_masks='release' in summary,flag_absent=True,within_cap=True,phase_counts=dict(Counter(r['phase'] for r in actual)))
g.write('audit.json',report)
print(json.dumps(report,indent=2))
# Separate inherited40c syntax/coarse scorer and exact40e input-token comparison.
old_rows=[json.loads(s) for s in (g.e.OUT/'records.jsonl').read_text().splitlines()]
old_off={r['task_id']:r for r in old_rows if r['pair']=='P1' and r['phase']=='screen' and r['arm']=='OFF'}
comparison=[]
for r in rows:
 t=dict(tasks[r['task_id']],witness=r'[+*\-]')
 syntax=g.base.score(r['text'],t,r['truncated'])
 assert syntax['valid_language']==r['score']['valid_skill']
 assert r['input_token_ids']==old_off[r['task_id']]['input_token_ids']
 phases={}
 for phase in ('prefill','decode'):
  ds=[v for k,v in r['dispatch'].items() if k.endswith(phase)]
  total=sum(v['tokens'] for v in ds);changed=sum(v['changed_route_tokens'] for v in ds)
  phases[phase]=dict(layer_tokens=total,changed_layer_tokens=changed,fraction=changed/total)
 comparison.append(dict(task_id=r['task_id'],skill=r['score']['valid_skill'],check40c_scorer=syntax['valid_language'],check40c_coarse=syntax['valid_task'],prior40e_OFF=old_off[r['task_id']]['score']['valid_skill'],exact40e_input_token_ids=True,dispatch=phases))
assert len(comparison)==8 and control<6
report.pop('paired_decisions')
report.update(pair_screens_audited=0,independent40c_scorer_agreement=8,exact40e_input_token_matches=8)
g.write('audit.json',report)
g.write('control-comparison.json',comparison)
print('Independent40c scorer and exact40e input-token comparison: 8/8 PASS')
