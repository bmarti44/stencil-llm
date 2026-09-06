"""Literal pilot3 DEV replay; never construct evaluation episodes."""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import tempfile
from stencil.focus import slab

OUT = Path(__file__).resolve().parent
OLD = OUT.parent/'composition-pilot-3'


def main():
    sources = [OLD/'records.jsonl', OLD/'continuation/records.jsonl']
    lanes = defaultdict(list)
    manifests = []
    for path in sources:
        manifests.append(dict(path=str(path), size=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        for line in path.open():
            row = json.loads(line)
            d = row['oracle_checker_results'][0]
            assert d['episode'].startswith('slab-dev-')
            lanes[d['episode'],d['arm']].append(row)
    records = []; stats = defaultdict(Counter)
    with tempfile.TemporaryDirectory() as temp:
        for (episode, arm), rows in sorted(lanes.items()):
            e = slab.generate_episode('dev', int(episode.rsplit('-',1)[1]))
            directory = Path(temp)/episode/arm
            slab.materialize(e, directory)
            ex = slab.Executor(directory, json.loads((directory/'public_tests.json').read_text()))
            for row in sorted(rows, key=lambda r:r['oracle_checker_results'][0]['round']):
                d = row['oracle_checker_results'][0]; i = d['round']
                result = ex.run(row['output'])
                outcome = slab.check(e, i, row['output'], ex, truncated=row['truncated'])
                stats[arm].update(calls=1, original_executed=bool(d['execution']['executed']), amended_executed=bool(result['executed']), caps=bool(row['truncated']))
                stats[arm].update({'violation_'+k:int(v) for k,v in outcome['violations'].items()})
                records.append(dict(episode=episode, arm=arm, round=i, output_sha256=hashlib.sha256(row['output'].encode()).hexdigest(), executed=len(result['executed']), tolerances=result['tolerances'], outcome=outcome, truncated=row['truncated']))
    assert len(records)==460 and len({(r['episode'],r['arm'],r['round']) for r in records})==460
    assert {a:s['caps'] for a,s in stats.items()}=={'R':59,'N':82,'T':52}
    (OUT/'regression-records.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in records))
    summary=dict(sources=manifests, arms=stats, calls=len(records), interpretation='Literal outputs replayed on amended per-lane state; not new model trajectories; caps unchanged.')
    (OUT/'regression.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(stats,indent=2))


if __name__=='__main__':main()
