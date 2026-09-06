"""Read-only progress from pilot4 journals."""
from collections import Counter, defaultdict
import json
from pathlib import Path
import time

OUT=Path(__file__).resolve().parent

def main():
    phases=[OUT]+([OUT/'continuation'] if (OUT/'continuation/run.json').exists() else [])
    runs=[json.loads((phase/'run.json').read_text()) for phase in phases]
    print('status',runs[-1]['status'],'total_held_seconds',round(sum(r.get('end',time.time())-r['start'] for r in runs)))
    for phase in phases:
        for name in ('cold-reverse.json','determinism.json'):
            path=phase/name
            if path.exists():
                r=json.loads(path.read_text());print(phase.name,name,'passed',r['passed'],'D',r['D'])
    stats=defaultdict(Counter);latest=None
    for path in [phase/'records.jsonl' for phase in phases if (phase/'records.jsonl').exists()]:
        for line in path.open():
            try:r=json.loads(line)
            except ValueError:continue
            d=r['oracle_checker_results'][0];a=stats[d['arm']]
            a.update(calls=1,executed=bool(d['execution']['executed']),caps=bool(r['truncated']),round_success=bool(d['outcome']['success']))
            latest=(d['episode'],d['arm'],d['round'])
    print('arms',dict(stats),'latest',latest)
    log=(phases[-1]/'run.log').read_text();print(log[-350:])

if __name__=='__main__':main()
