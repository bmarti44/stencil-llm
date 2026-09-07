"""Read-only source/saved-record checks, no model or held-out source reads."""
import json
import sys
from pathlib import Path
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P))
import convert as c
import runner as r

def main():
    frozen=json.loads((P/'freeze.json').read_text())
    changed=[]
    for path,d in frozen['sha256'].items():
        if path.endswith('check48/README.md'):continue # outcome appended after run
        if c.sha(c.R/path)!=d:changed.append(path)
    assert not changed,changed
    files={};failures=0
    for path in P.glob('*-records.jsonl'):
        if path.name=='training-records.jsonl':continue
        rows=c.rows(path)
        for rec in rows:
            assert c.visible(rec['input'])==rec['visible']
            raw='[]' if rec['role_guard'] else rec['raw']
            finish='stop' if rec['role_guard'] else rec['finish_reason']
            assert r.parse(raw,rec['input'],finish)==rec['parsed']
            failures+=bool(rec['parsed']['failure'])
        assert path.stat().st_size<=10_000_000
        files[path.name]={'records':len(rows),'sha256':c.sha(path)}
    adapter=P/'adapter-manifest.json'
    if adapter.exists():
        for path,d in json.loads(adapter.read_text()).get('sha256',{}).items():assert c.sha(c.R/path)==d
    out=dict(frozen_sources_match=True,record_replays=files,parser_failures=failures,own_flag_absent=not (P/'RUNNING.flag').exists())
    c.write('audit.json',out);print(json.dumps(out,indent=2))

if __name__=='__main__':main()
