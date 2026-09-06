"""Run the complete scheduling and episode receipt consumer on DEV references."""
import importlib.util
from pathlib import Path
import tempfile
import time
OUT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('runner',OUT/'run.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
class Stub:
    def __init__(self,client,tokenizer,deadline,lane,wave):self.lane,self.wave=lane,wave
    def __call__(self,req):
        l=self.lane;text=r.slab.reference(l.episode,l.round);ids=r.slab.qwen_encode(text)
        assert len(req.prompt_ids)<=l.bound<=32768-512
        l.measurement=dict(total_tokens=len(ids)+1,wave=self.wave,cpu_stub=True)
        return r.p.tool_calls(r.DecodeResult(text,ids,151645,False))
r.Decoder=Stub
with tempfile.TemporaryDirectory() as d:
    r.OUT=Path(d);r.trajectories(None,time.time()+9000,None)
    import json
    rows=[json.loads(x) for x in (r.OUT/'records.jsonl').read_text().splitlines()]
    eps=[json.loads(x) for x in (r.OUT/'episodes.jsonl').read_text().splitlines()]
    assert len(rows)==640 and len(eps)==32
    assert all(e['complete'] for e in eps)
    assert all(x['oracle_checker_results'][0]['outcome']['success'] for x in rows)
    assert all(e['output_sha256'] and e['transcript_sha256'] for e in eps)
    r.p.write(OUT/'schedule-smoke.json',dict(passed=True,records=len(rows),episodes=len(eps),
        all_final_success=True,all_transcript_and_output_hashes=True,dev_only=True))
print('PASS complete 640-round CPU schedule including episode hash writer')
