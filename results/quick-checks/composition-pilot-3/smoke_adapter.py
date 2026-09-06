"""Exercise the actual adapter's body/EOS/cap semantics with synthetic HTTP receipts."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
OUT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('runner',OUT/'run.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
tok=r.Tokenizer.from_file(str(r.slab.TOKENIZER_PATH))
checks=0
for arm in 'RNTO':
    for eos in (151645,151643,None):
        ids=[16,17,eos] if eos else [16]*512
        lane=SimpleNamespace(arm=arm,round=0,bound=100,episode=SimpleNamespace(episode_id='synthetic-dev'))
        def call(*args):
            return dict(complete=True,output_token_ids=ids,finish_reason='stop' if eos else 'length',started=0,
                wall_seconds=1,ttft_seconds=.1,decode_seconds=.9,decode_tokens=len(ids)-1)
        decoder=r.Decoder(SimpleNamespace(call=call),tok,9999999999,lane,0)
        result=decoder(SimpleNamespace(prompt_ids=(16,17)))
        assert result.eos==eos and result.truncated==(eos is None)
        assert list(result.output_ids)==(ids[:-1] if eos else ids)
        assert result.text==tok.decode(list(result.output_ids),skip_special_tokens=False)
        assert lane.measurement['transcript_sha256']==r.ids_hash([16,17]+ids)
        checks+=1
r.p.write(OUT/'adapter-smoke.json',dict(passed=True,cases=checks,arms=list('RNTO'),EOS=[151645,151643],cap=512))
print('PASS',checks,'actual adapter cases')
