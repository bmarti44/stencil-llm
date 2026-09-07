"""CPU-only replay through the frozen check49 scorer and production renderer."""
import importlib.util
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('check51', OUT/'run.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def main():
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(m.h.BASE,local_files_only=True)
    inputs = json.loads((OUT/'inputs.json').read_text())
    assert inputs == m.cases()
    records = [json.loads(x) for x in (OUT/'records.jsonl').read_text().splitlines()]
    assert len(records)==8 and len({r['id'] for r in records})==8
    for row,r in zip(inputs,records):
        assert r['id']==row['id']
        assert tok.encode(m.h.render(tok,row['messages']),add_special_tokens=False)==r['input_ids']
        assert tok.decode(r['token_ids'],skip_special_tokens=True)==r['text']
        score = m.h.execute(row['tasks'][2],r['text'])
        assert all(r[k]==v for k,v in score.items())
        assert r['copied_structure']==(m.structure(r['text'])==m.structure(row['tasks'][1]['references'][row['initial']]))
        assert r['first_divergence']==m.divergence(tok,r['token_ids'],row['retained_continuation'])
        assert r['success']==(score['language']==row['target'] and score['semantics'] and not r['truncated'])
    summary=json.loads((OUT/'summary.json').read_text())
    assert summary['status']=='COMPLETE' and summary['calls']==8
    assert summary['successes']==sum(r['success'] for r in records)
    assert summary['gpu_held_seconds']<600
    report=dict(records_replayed=8, input_renderer_replays=8, score_replays=8, divergence_replays=8, all_checks_passed=True, records_bytes=(OUT/'records.jsonl').stat().st_size)
    assert report['records_bytes']<10_000_000
    m.h.write(OUT/'audit.json',report)
    print(json.dumps(report))


if __name__=='__main__':
    main()
