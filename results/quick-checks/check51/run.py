"""Eight text-only setup SWITCH controls; CPU prepare before GPU run."""
import argparse
import gc
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / 'src')]
spec = importlib.util.spec_from_file_location('check49', ROOT / 'scripts/focus_check49.py')
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)  # main-guarded; no prepare/run/evaluation calls
from stencil.focus.register import Entry, Register, Scope, Source
from stencil.focus.renderer import Request, render


def cases():
    bank = {t['family']: t for t in h.setup()}
    rows = []
    for family in ['square', 'negate', 'lengths', 'product']:
        original = bank[family]
        tasks = []
        for k in [2, 3, 4]:
            t = json.loads(json.dumps(original))
            t['id'] = f'check51/{family}/{k}'
            t['prompt'] += f' Then add {k} to ' + ('each returned element.' if family in ['negate', 'lengths'] else 'the returned number.')
            for c in t['cases']:
                c['expected'] = [v+k for v in c['expected']] if isinstance(c['expected'], list) else c['expected']+k
            py, js = {
                'square': (f'return n*n + {k}', f'return n*n + {k};'),
                'negate': (f'return [-x + {k} for x in xs]', f'return xs.map(x => -x + {k});'),
                'lengths': (f'return [len(s) + {k} for s in xs]', f'return xs.map(s => s.length + {k});'),
                'product': (f'p = 1\n    for x in xs: p *= x\n    return p + {k}', f'let p=1; for (const x of xs) p*=x; return p + {k};'),
            }[family]
            t['references'] = {'python': f'```python\ndef {t["name"]}({t["prompt"].split("(",1)[1].split(")",1)[0]}):\n    {py}\n```', 'js': f'```javascript\nfunction {t["name"]}({t["prompt"].split("(",1)[1].split(")",1)[0]}) {{ {js} }}\n```'}
            tasks.append(t)
        for a, b in [('python', 'js'), ('js', 'python')]:
            history = []
            for i, t in enumerate(tasks[:2]):
                if i == 1:
                    history += h.NEUTRAL
                history += [{'role':'user','content':t['prompt']}, {'role':'assistant','content':t['references'][a]}]
            language = 'Python' if b == 'python' else 'JavaScript'
            reg = Register().apply([Entry('add','code-language',Scope(request_kinds=('code_answer',)), 'language',language,'check51-switch',Source('user','switch'),f'Write all code in {language}.')])
            user = render(reg, Request(tasks[2]['prompt'], 'code_answer')).text
            msgs = h.messages(tasks[2], history)
            msgs[-1]['content'] = user
            rows.append(dict(id=f'{family}/{a}-to-{b}', family=family, initial=a, target=b, tasks=tasks, messages=msgs, retained_continuation=tasks[2]['references'][a]))
    return rows


def structure(text):
    # Exact lexical structure modulo whitespace and numeric constants, language retained.
    return re.findall(r'\w+|[^\w\s]', re.sub(r'\b\d+(?:\.\d+)?\b', '<NUM>', text))


def divergence(tok, output, continuation):
    expected = tok.encode(continuation, add_special_tokens=False) + [tok.eos_token_id]
    p = next((i for i, (a,b) in enumerate(zip(output,expected)) if a != b), min(len(output),len(expected)))
    def token(ids):
        return None if p == len(ids) else dict(id=ids[p], piece=tok.convert_ids_to_tokens(ids[p]), decoded=tok.decode([ids[p]]))
    return dict(position_zero_based=p, generated=token(output), retained_continuation=token(expected), identical=output==expected)


def prepare():
    rows = cases()
    assert len(rows) == 8
    checked = 0
    for row in rows:
        for t in row['tasks']:
            for lang, ref in t['references'].items():
                score = h.execute(t, ref)
                assert score['semantics'] and score['language'] == lang, (row['id'],score)
                checked += 1
        assert structure(row['tasks'][1]['references'][row['initial']]) == structure(row['retained_continuation'])
        assert row['messages'][0]['content'] == h.SYSTEM
        assert row['messages'][-1]['content'].endswith(row['tasks'][2]['prompt'])
        assert 'Active rules for this request' in row['messages'][-1]['content']
        assert not h.execute(row['tasks'][2],row['tasks'][1]['references'][row['initial']])['semantics']
    h.write(OUT/'inputs.json', rows)
    h.write(OUT/'freeze.json',dict(code_sha256=h.sha(Path(__file__)), harness_sha256=h.sha(ROOT/'scripts/focus_check49.py'), renderer_sha256=h.sha(ROOT/'src/stencil/focus/renderer.py'), inputs_sha256=h.sha(OUT/'inputs.json'), reference_checks=checked, generation_cap=8, output_cap=96, gpu_cap_s=600))
    print(f'CPU validated {checked} references, 8 stale-constant failures, histories and rendering')


def run():
    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer, StoppingCriteria, StoppingCriteriaList
    freeze = json.loads((OUT/'freeze.json').read_text())
    assert freeze['code_sha256'] == h.sha(Path(__file__))
    assert freeze['harness_sha256'] == h.sha(ROOT/'scripts/focus_check49.py')
    assert freeze['renderer_sha256'] == h.sha(ROOT/'src/stencil/focus/renderer.py')
    assert freeze['inputs_sha256'] == h.sha(OUT/'inputs.json')
    assert not (OUT/'records.jsonl').exists()
    assert not list((ROOT/'results/quick-checks').glob('*/RUNNING.flag')), 'GPU flag occupied; retry before any model load'
    flag = OUT/'RUNNING.flag'
    with flag.open('x') as f:
        f.write(json.dumps(dict(pid=os.getpid(), purpose='check51 eight setup text controls', cap_s=600)))
    with (ROOT/'.stencil-owned-pids').open('a') as f:
        f.write(str(os.getpid())+'\n')
    start = time.monotonic()
    model = None
    records = []
    summary = dict(status='INCOMPLETE', torch=torch.__version__, transformers=transformers.__version__)
    class Deadline(StoppingCriteria):
        def __call__(self, input_ids, scores, **kwargs):
            return time.monotonic()-start > 540
    try:
        assert list((ROOT/'results/quick-checks').glob('*/RUNNING.flag')) == [flag]
        torch.set_num_threads(8)
        torch.manual_seed(0)
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        torch.use_deterministic_algorithms(True)
        tok = AutoTokenizer.from_pretrained(h.BASE,local_files_only=True)
        model = AutoModelForCausalLM.from_pretrained(h.BASE,local_files_only=True,dtype=torch.bfloat16,attn_implementation='sdpa').to('cuda').eval()
        model.requires_grad_(False)
        assert all(not p.requires_grad for p in model.parameters())
        summary['load_s'] = time.monotonic()-start
        for row in json.loads((OUT/'inputs.json').read_text()):
            if time.monotonic()-start > 500:
                raise RuntimeError('cooperative budget reserve')
            ids = tok(h.render(tok,row['messages']),return_tensors='pt',add_special_tokens=False).to('cuda')
            begin = time.monotonic()
            with torch.inference_mode():
                out = model.generate(**ids,max_new_tokens=96,do_sample=False,use_cache=True,pad_token_id=tok.eos_token_id,eos_token_id=tok.eos_token_id,stopping_criteria=StoppingCriteriaList([Deadline()]))
            torch.cuda.synchronize()
            tokens = out[0,ids.input_ids.shape[1]:].tolist()
            text = tok.decode(tokens,skip_special_tokens=True)
            score = h.execute(row['tasks'][2],text)
            capped = len(tokens)>=96 and tokens[-1]!=tok.eos_token_id
            r = dict(id=row['id'], target=row['target'], initial=row['initial'], text=text, token_ids=tokens, input_ids=ids.input_ids[0].tolist(), seconds=time.monotonic()-begin, truncated=capped, **score)
            r['success'] = score['language']==row['target'] and score['semantics'] and not capped
            r['copied_structure'] = structure(text)==structure(row['tasks'][1]['references'][row['initial']])
            r['first_divergence'] = divergence(tok,tokens,row['retained_continuation'])
            assert all(k in r for k in ['language','semantics','copied_structure','first_divergence'])
            with (OUT/'records.jsonl').open('a') as f:
                f.write(json.dumps(r)+'\n'); f.flush(); os.fsync(f.fileno())
            records.append(r)
            print(json.dumps(r),flush=True)
        n = sum(r['success'] for r in records)
        summary.update(status='COMPLETE',successes=n,reading='CONTROL-PASS' if n>=6 else 'CONTROL-FAIL' if n<=3 else 'INCONCLUSIVE',calls=len(records), language_switches=sum(r['language']==r['target'] for r in records), semantics=sum(r['semantics'] for r in records), copied_structure=sum(r['copied_structure'] for r in records), truncations=sum(r['truncated'] for r in records), peak_allocated_bytes=torch.cuda.max_memory_allocated())
    finally:
        del model
        gc.collect()
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
        summary['gpu_held_seconds'] = time.monotonic()-start
        h.write(OUT/'summary.json', summary)
        flag.unlink()
        print(json.dumps(summary),flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command',choices=['prepare','run'])
    args = parser.parse_args()
    prepare() if args.command=='prepare' else run()
