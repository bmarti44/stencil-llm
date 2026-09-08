import concurrent.futures, hashlib, json, os, time, urllib.request
from pathlib import Path
ROOT = Path('/home/bmarti44/stencil-llm')
BASE = ROOT/'results/coding-competence'
ENDPOINT = 'http://127.0.0.1:11434/api/generate'
def save(path, obj):
    raw=(json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode()
    tmp=path.with_suffix(path.suffix+'.tmp')
    with tmp.open('wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    tmp.replace(path)
def one(index):
    folder=BASE/f'author-{index:02d}'
    request=(folder/'request.json').read_bytes()
    assert not (folder/'response.json').exists()
    receipt={'purpose':'user-authorized wholly new Kimi K3 competence DEV authoring','pid':os.getpid(),'started_unix':time.time(),'endpoint':ENDPOINT,'request_sha256':hashlib.sha256(request).hexdigest(),'status':'RUNNING'}
    save(folder/'receipt.json',receipt)
    try:
        req=urllib.request.Request(ENDPOINT,data=request,headers={'Content-Type':'application/json'},method='POST')
        with urllib.request.urlopen(req,timeout=1800) as response:
            raw=response.read(); receipt['http_status']=response.status
        with (folder/'response.json').open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
        receipt['response_sha256']=hashlib.sha256(raw).hexdigest()
        obj=json.loads(raw)
        for key in ['done','done_reason','prompt_eval_count','eval_count','total_duration','load_duration','prompt_eval_duration','eval_duration']:
            if key in obj:receipt[key]=obj[key]
        value=obj.get('response','')
        receipt['response_text_sha256']=hashlib.sha256(value.encode()).hexdigest()
        stripped=value.strip()
        if stripped.startswith('```json\n') and stripped.endswith('\n```'):
            stripped=stripped[len('```json\n'):-len('\n```')]
            receipt['extraction']='remove exactly one outer JSON Markdown fence; no semantic edits'
        else:receipt['extraction']='parse JSON response text; no semantic edits'
        document=json.loads(stripped)
        if not isinstance(document,dict):raise ValueError('one project must be a JSON object')
        save(folder/'authored.json',document)
        receipt['authored_sha256']=hashlib.sha256((folder/'authored.json').read_bytes()).hexdigest()
        receipt['status']='AUTHORED_UNREVIEWED'
    except Exception as exc:
        receipt['status']='ERROR';receipt['error']=f'{type(exc).__name__}: {exc}'
    finally:
        receipt['elapsed_seconds']=time.time()-receipt['started_unix']
        save(folder/'receipt.json',receipt)
    print(json.dumps({'author':index,'status':receipt['status'],'seconds':round(receipt['elapsed_seconds'],3),'error':receipt.get('error')}),flush=True)
    return receipt['status']
def main():
    with (ROOT/'.stencil-owned-pids').open('a') as f:f.write(f'{os.getpid()}\n');f.flush();os.fsync(f.fileno())
    print(f'Owned Kimi authoring PID {os.getpid()}',flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        statuses=list(pool.map(one,range(4)))
    return 0 if all(s=='AUTHORED_UNREVIEWED' for s in statuses) else 2
if __name__=='__main__':raise SystemExit(main())
