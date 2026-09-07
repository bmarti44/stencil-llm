"""HF5-compatible LM Format Enforcer prefix adapter.

Installed upstream integration imports a removed HF4 tokenizer alias; use the
same public TokenEnforcer API and tokenizer decoding convention locally.
"""
from lmformatenforcer import TokenEnforcer, TokenEnforcerTokenizerData


def build_token_enforcer_tokenizer_data(tokenizer):
    zero=tokenizer.encode('0',add_special_tokens=False)[-1]
    special=set(tokenizer.all_special_ids)
    regular=[]
    for i in range(len(tokenizer)):
        if i in special:continue
        after=tokenizer.decode([zero,i])[1:]
        alone=tokenizer.decode([i])
        regular.append((i,after,len(after)>len(alone)))
    def decode(ids):return tokenizer.decode(ids).rstrip('�')
    return TokenEnforcerTokenizerData(regular,decode,tokenizer.eos_token_id,False,len(tokenizer))


def build_transformers_prefix_allowed_tokens_fn(td,parser):
    enforcer=TokenEnforcer(td,parser)
    def prefix(batch_id,ids):
        return enforcer.get_allowed_tokens(ids.tolist()).allowed_tokens
    return prefix
