"""Inside qualified image: test actual XGrammar consumer, including quoted spans."""
import json,sys
import xgrammar as xg
payload=json.load(sys.stdin)
ti=xg.TokenizerInfo([bytes([i]) for i in range(256)]+[b'<eos>'],stop_token_ids=[256])
compiler=xg.GrammarCompiler(ti)
compiled=compiler.compile_grammar(xg.Grammar.from_ebnf(payload['grammar']))
results=[]
for case in payload['cases']:
 matcher=xg.GrammarMatcher(compiled)
 accepted=matcher.accept_string(case['text']) and matcher.accept_token(256)
 assert accepted==case['accept'],case
 results.append({'accept':accepted,'expected':case['accept']})
print(json.dumps({'passed':len(results),'cases':results}))
