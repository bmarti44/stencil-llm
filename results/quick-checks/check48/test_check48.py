import importlib.util
import json
import sys
from pathlib import Path
import pytest
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P))
import convert as c
import runner as r

def test_replacement_withdraw_and_decimal():
    assert c.replacement('Retire the old five-point scale; use low, medium, high bands on the chart instead.')=='low, medium, high bands on the chart'
    assert c.replacement('Scrap the old ceiling for the cycle guide and set ammonia at 0.5 ppm going forward.')=='set ammonia at 0.5 ppm'
    assert c.replacement('Ugh, scrap that — call them by their first name instead of valued member.')=='call them by their first name'
    assert c.replacement('Metric first going forward is annoying; switch needle sizes from metric-first to US-first for everything.')=='US-first for everything'
    assert c.replacement('Bring the withdrawal-period note back on medicine entries, but express it in days rather than doses.')=='express it in days'

def test_span_convention_and_ambiguous_quote():
    assert c.strip_cue('For the kiln journal, use short entries.')=='use short entries'
    assert c.strip_cue('Whenever I ask for a journal, use short entries.')=='Whenever I ask for a journal, use short entries'
    with pytest.raises(ValueError):c.span('cat cat','cat')

def test_no_gold_leak():
    row=dict(old_rule='Use dots',key='punctuation',scope='global',status='live',message='Use dashes',role='user',label='SECRET',why='SECRET',target_span='SECRET',id='SECRET')
    v=c.visible(row)
    assert 'SECRET' not in json.dumps(v)
    assert v['register'][0]['id']=='r1'

def test_schema_and_grounding():
    row=dict(message='Keep “RED”\n labels.',role='user')
    op=dict(op='add',span='keep "red" labels.',key='label',scope='global',kind='instruction',value='red',target_id=None)
    assert r.parse(json.dumps([op]),row,'stop')['accepted'][0]['match']=='normalized'
    assert r.parse(json.dumps([op]),row,'length')['failure']=='truncated'
    op['span']='blue';assert r.parse(json.dumps([op]),row,'stop')['rejected']
    op['extra']='x';assert r.parse(json.dumps([op]),row,'stop')['failure']=='json_or_schema'

def test_fixed_sample_and_consumer():
    fit=c.rows(P/'fit-transitions.jsonl');dev=c.rows(P/'dev-transitions.jsonl')
    assert len(fit)==2048 and len(dev)==128
    assert not {x['scenario_group'] for x in fit}&{x['scenario_group'] for x in dev}
    assert not {c.norm(x['input']['message']) for x in fit}&{c.norm(x['input']['message']) for x in dev}
    for rec in fit+dev:
        assert rec['input_tokens']+rec['output_tokens']<=768
        assert not rec['raw'].get('evaluation_derived')
        assert 'astra-enrich-2' not in rec['source_file']
        parsed=r.parse(json.dumps(rec['output']),rec['raw'],'stop')
        assert not parsed['failure'] and not parsed['rejected'],rec['id']
        assert len(parsed['accepted'])==len(rec['output'])
        for op in rec['output']:
            if op['op']=='supersedes':
                assert op['value'] in rec['input']['message']
                assert c.norm(op['value'])!=c.norm(rec['input']['message'])
            if op['op']=='add':assert not op['span'].endswith(tuple('.!?,;'))
