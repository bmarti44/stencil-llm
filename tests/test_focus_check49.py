"""Decision-rule and executable-consumer checks; no GPU or benchmark data."""
import copy
import importlib.util
from pathlib import Path

spec=importlib.util.spec_from_file_location('check49',Path(__file__).resolve().parents[1]/'scripts/focus_check49.py')
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def fixture():
    records=[]
    def row(key,lang='python',success=True,seconds=1,carrier=0):
        records.append(dict(id=key,success=success,semantics=success,truncated=False,language=lang,token_ids=[1],seconds=seconds,rule_carrier_positions=carrier,input_tokens=10,output_tokens=5))
    for i in range(12):
        for arm in ['M','T','X']:
            for stage in m.STAGES:
                row(f'episode/{i}/{arm}/{stage}',success=arm!='X',carrier=12 if arm=='T' and stage!='CLEAR' else 0)
        row(f'cold/{i}')
        row(f'fresh/{i}')
        row(f'replay/{i}')
    for i in range(8):
        row(f'sentinel/sentinel_{i}/None')
        row(f'sentinel/sentinel_{i}/{m.MODES[i%2]}')
    for i in range(40): row(f'setup/{i}')
    return records


def parity():
    return dict(logit_diffs=0,token_diffs=0,on_effects=16)


def test_full_gate_and_one_new_harm_blocks():
    r=fixture()
    assert len(r)==272
    assert m.analyze(r,parity())['status']=='GO'
    next(x for x in r if x['id']=='episode/0/M/HOLD')['semantics']=False
    assert not m.analyze(r,parity())['bars']['competence']


def test_three_discordances_fail_exact_test_and_five_pass():
    r=fixture()
    for x in r:
        if x['id'].startswith('episode/') and '/X/' in x['id'] and int(x['id'].split('/')[1])>=3:
            x['success']=True
    a=m.analyze(r,parity())
    assert a['paired_M_X']['p']==.125
    assert not a['bars']['mechanism']
    for x in r:
        if '/X/' in x['id'] and int(x['id'].split('/')[1]) in [3,4]: x['success']=False
    assert m.analyze(r,parity())['paired_M_X']['p']==.03125


def test_stale_clear_and_replay_cannot_certify_release():
    r=fixture()
    for x in r:
        if x['id']=='episode/1/M/CLEAR': x['language']='js'
    assert not m.analyze(r,parity())['bars']['clear']
    assert not m.analyze(fixture(),dict(logit_diffs=0,token_diffs=0,on_effects=0))['bars']['clear']


def test_scoring_does_not_mutate_test_inputs():
    t=m.setup()[1]
    before=copy.deepcopy(t)
    result=m.execute(t,f"```python\ndef {t['name']}(xs):\n    xs.reverse()\n    return xs\n```")
    assert result['semantics']
    assert t==before


def test_language_and_presentation_separate_from_semantics():
    t=m.setup()[0]
    r=m.execute(t,t['references']['js'])
    assert r['semantics'] and r['language']=='js'
    r=m.execute(t,t['references']['python'].split('\n',1)[1].rsplit('\n',1)[0])
    assert r['semantics'] and not r['presentation']
