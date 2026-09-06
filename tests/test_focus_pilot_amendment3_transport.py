"""Additional post-freeze transport tests; inference sources unchanged."""
import pytest
from stencil.focus import slab
from test_focus_pilot_amendment3 import executor


@pytest.mark.parametrize('text', ['{"calls":[],"report":', '{"calls":[],"report":{"status":True}}', '[]}', '{"calls":[],"report":{}};'])
def test_incomplete_literals_nonobject_and_other_suffix_not_repaired(tmp_path, text):
    e, ex = executor(tmp_path)
    result = ex.run(text)
    assert not result['executed'] and not result['tolerances']
    assert result['results'][0]['error']=='envelope'


def test_edit_function_state_reaches_actual_next_prompt(tmp_path):
    from scripts import composition_pilot as p
    from stencil.focus.loop import DecodeResult, generate_once
    e=slab.generate_episode('dev', 0)
    lane=p.Lane(tmp_path,e,'R','test')
    for i in range(2):
        lane.prepare(i);lane.gate=dict(allowed=True,bounds={'R':lane.bound})
        def decoder(req):
            if i==1:
                assert '"functions":["identity","step_0"]' in slab.qwen_tokenizer().decode(list(req.prompt_ids))
            text=slab.reference(e,i)
            return p.tool_calls(DecodeResult(text,slab.qwen_encode(text),151645,False))
        generate_once(lane.session,lane.messages,decoder,tools=p.TOOL_SCHEMA)
        assert lane.rows[-1]['oracle_checker_results'][0]['outcome']['success']
