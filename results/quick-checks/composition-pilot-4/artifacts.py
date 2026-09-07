"""Manifest local streams and oversized files; shard exact per-call records."""
import hashlib
import json
from pathlib import Path

OUT=Path(__file__).resolve().parent
LIMIT=10_000_000


def main():
    for source in [p for p in (OUT/'records.jsonl',OUT/'continuation/records.jsonl') if p.exists()]:
        shards=source.parent/'records';shards.mkdir(exist_ok=True)
        index=0;parts=[];size=0
        for line in source.open('rb'):
            assert len(line)<=LIMIT
            if size+len(line)>8_000_000:
                (shards/f'{index:03}.jsonl').write_bytes(b''.join(parts));index+=1;parts=[];size=0
            parts.append(line);size+=len(line)
        if parts:(shards/f'{index:03}.jsonl').write_bytes(b''.join(parts))
    manifest=[]
    for path in sorted(OUT.rglob('*')):
        if not path.is_file() or '__pycache__' in path.parts or path.name=='artifact-manifest.json':continue
        rel=path.relative_to(OUT)
        local=(('http' in rel.parts and path.suffix!='.prom') or path.stat().st_size>LIMIT or path.name in ('records.jsonl','RUNNING.flag') or 'c4' in rel.parts)
        manifest.append(dict(path=str(rel),size=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),commit=not local))
    (OUT/'artifact-manifest.json').write_text(json.dumps(dict(files=manifest,limit_bytes=LIMIT,record_shards='records/*.jsonl are exact sequential bytes of local records.jsonl; HTTP and workspaces remain local'),indent=2)+'\n')


if __name__=='__main__':main()
