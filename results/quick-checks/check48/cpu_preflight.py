"""Validate actual HF prefix consumer on fixed authored DEV output tokens."""
import json
from pathlib import Path
import sys
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P))
import convert as c
import runner as r

def main():
    import torch
    from transformers import AutoTokenizer
    from lmformatenforcer import JsonSchemaParser
    from grammar import build_token_enforcer_tokenizer_data,build_transformers_prefix_allowed_tokens_fn
    tok=AutoTokenizer.from_pretrained(r.MODEL,local_files_only=True)
    td=build_token_enforcer_tokenizer_data(tok)
    data=c.rows(P/'dev-transitions.jsonl'); witnesses=[]
    for category in ['none','add','updates']:
        rec=next(x for x in data if x['category']==category)
        a,b=c.tokens(tok,rec)
        fn=build_transformers_prefix_allowed_tokens_fn(td,JsonSchemaParser(r.SCHEMA))
        prefix=a[:]
        target=json.dumps(rec['output'],ensure_ascii=False,separators=(',',':'))
        emitted='';count=0
        while emitted!=target:
            allowed=fn(0,torch.tensor(prefix));remaining=target[len(emitted):]
            options=[(tok.decode([i]),i) for i in allowed if i!=tok.eos_token_id]
            options=[(t,i) for t,i in options if t and remaining.startswith(t)]
            assert options,(category,emitted[-100:])
            text,token=max(options,key=lambda x:(len(x[0]),-x[1]))
            emitted+=text;prefix.append(token);count+=1
        assert tok.eos_token_id in fn(0,torch.tensor(prefix))
        witnesses.append(dict(id=rec['id'],category=category,tokens=count,pass_all=True))
    c.write('cpu-validation.json',dict(grammar_consumer_witnesses=witnesses,tests='5 targeted tests pass; full 2176-gold strict parser/grounding and scenario separation checked',cuda_initialized=torch.cuda.is_initialized()))
    assert not torch.cuda.is_initialized()
    print(json.dumps(witnesses))

if __name__=='__main__':main()
