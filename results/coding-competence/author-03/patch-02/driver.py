"""Preserve Kimi correction exchanges and apply exact guarded field replacements."""
import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path('/home/bmarti44/stencil-llm')
BASE = ROOT / 'results/coding-competence'
ENDPOINT = 'http://127.0.0.1:11434/api/generate'


def value_hash(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def save(path, value):
    if path.exists():
        raise FileExistsError(path)
    with path.open('x', encoding='utf-8') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write('\n')
        handle.flush()
        os.fsync(handle.fileno())


def receipt_write(path, value):
    temp = path.with_suffix('.tmp')
    with temp.open('w', encoding='utf-8') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write('\n')
        handle.flush()
        os.fsync(handle.fileno())
    temp.replace(path)


def parent_at(document, pointer):
    parts = pointer.strip('/').split('/')
    current = document
    for part in parts[:-1]:
        current = current[int(part)] if isinstance(current, list) else current[part]
    key = int(parts[-1]) if isinstance(current, list) else parts[-1]
    return current, key


def one(index):
    folder = BASE / f'author-{index:02d}'
    dest = folder / 'patch-02'
    request = (dest / 'request.json').read_bytes()
    original_bytes = (folder / 'patch-01/patched.json').read_bytes()
    metadata = json.loads((dest / 'allowed-paths.json').read_text())
    assert hashlib.sha256(original_bytes).hexdigest() == metadata['original_sha256']
    assert not (dest / 'response.json').exists()
    receipt = {'pid': os.getpid(), 'started_unix': time.time(), 'status': 'RUNNING',
               'purpose': 'Kimi-only bounded semantic corrections before worker exposure',
               'endpoint': ENDPOINT, 'request_sha256': hashlib.sha256(request).hexdigest(),
               'original_sha256': metadata['original_sha256']}
    receipt_write(dest / 'receipt.json', receipt)
    try:
        req = urllib.request.Request(ENDPOINT, data=request,
                                     headers={'Content-Type': 'application/json'}, method='POST')
        try:
            with urllib.request.urlopen(req, timeout=1800) as response:
                raw = response.read()
                receipt['http_status'] = response.status
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            receipt['http_status'] = exc.code
            with (dest / 'response.json').open('xb') as handle:
                handle.write(raw)
                handle.flush()
                os.fsync(handle.fileno())
            receipt['response_sha256'] = hashlib.sha256(raw).hexdigest()
            raise
        with (dest / 'response.json').open('xb') as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        receipt['response_sha256'] = hashlib.sha256(raw).hexdigest()
        response = json.loads(raw)
        for key in ['done', 'done_reason', 'prompt_eval_count', 'eval_count', 'total_duration']:
            if key in response:
                receipt[key] = response[key]
        if response.get('done') is not True:
            raise ValueError('Ollama response is not terminal')
        body = response.get('response', '').strip()
        receipt['extraction'] = 'parse JSON only; no semantic edits'
        if body.startswith('```json\n') and body.endswith('\n```'):
            body = body[len('```json\n'):-len('\n```')]
            receipt['extraction'] = 'remove exactly one outer JSON fence; no semantic edits'
        patches = json.loads(body)
        save(dest / 'patches.json', patches)
        if not isinstance(patches, list) or len(patches) != 3:
            raise ValueError('expected nonempty replacement array')
        document = json.loads(original_bytes)
        applied = []
        seen = set()
        for patch in patches:
            if not isinstance(patch, dict) or set(patch) != {'path', 'old_sha256', 'value'}:
                raise ValueError('invalid patch keys')
            path = patch['path']
            if path not in metadata['allowed_old_sha256'] or path in seen:
                raise ValueError(f'disallowed or repeated exact path: {path}')
            parent, key = parent_at(document, path)
            expected = metadata['allowed_old_sha256'][path]
            if patch['old_sha256'] != expected or value_hash(parent[key]) != expected:
                raise ValueError(f'exact old-value hash mismatch: {path}')
            seen.add(path)
            parent[key] = patch['value']
            applied.append({'path': path, 'old_sha256': expected, 'new_sha256': value_hash(parent[key])})
        assert (folder / 'patch-01/patched.json').read_bytes() == original_bytes
        save(dest / 'patched.json', document)
        new_hash = hashlib.sha256((dest / 'patched.json').read_bytes()).hexdigest()
        save(dest / 'application.json', {'original_sha256': metadata['original_sha256'],
                                       'patched_sha256': new_hash, 'operations': applied,
                                       'semantic_author': 'kimi-k3:cloud', 'status': 'UNREVIEWED'})
        receipt['patched_sha256'] = new_hash
        receipt['replacements'] = len(applied)
        receipt['status'] = 'PATCHED_UNREVIEWED'
    except Exception as exc:
        receipt['status'] = 'ERROR'
        receipt['error'] = f'{type(exc).__name__}: {exc}'
    finally:
        receipt['elapsed_seconds'] = time.time() - receipt['started_unix']
        receipt_write(dest / 'receipt.json', receipt)
    print(json.dumps({'author': index, 'status': receipt['status'],
                      'seconds': round(receipt['elapsed_seconds'], 3),
                      'error': receipt.get('error')}), flush=True)
    return receipt['status']


def main():
    with (ROOT / '.stencil-owned-pids').open('a') as handle:
        handle.write(f'{os.getpid()}\n')
        handle.flush()
        os.fsync(handle.fileno())
    print(f'Owned Kimi correction PID {os.getpid()}', flush=True)
    statuses = [one(3)]
    return 0 if all(status == 'PATCHED_UNREVIEWED' for status in statuses) else 2


if __name__ == '__main__':
    raise SystemExit(main())
