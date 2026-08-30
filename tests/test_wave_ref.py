# ruff: noqa: E501
"""W0.0 canonical reference builder — red-first.

Registered form (INTERNAL-WAVE-PLAN v3): name {prefix}_{fn} (bare {fn}
if prefix inactive); docstring ALWAYS present, opening with the doc
value when active else the neutral opener "Compute." (not in POOLS);
args typed with the hint value when active, untyped otherwise; body
implements sess.ops[wt]. Must parse, execute (OP_TESTS), satisfy every
active obligation via score_work, and trip NO stale obligation."""
import ast

from stencil.qwen_task import DOC_OPENERS
from stencil.t2_runner import OP_TESTS, score_work
from stencil.t2_sessions import generate_t2
from stencil.wave_ref import canonical_code


def _session_with_work(seed):
    s = generate_t2(seed, 20, "dev", interference="s0")
    return s, s.work_turns[-1]


def test_neutral_opener_not_in_pools():
    assert "Compute" not in DOC_OPENERS


def test_canonical_respects_active_ledger():
    for seed in (13_400_000, 13_400_001, 13_400_002, 13_400_007):
        s, wt = _session_with_work(seed)
        code = canonical_code(s, wt)
        tree = ast.parse(code)
        fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
        led = s.ledger_at[wt]
        if "prefix" in led:
            assert fn.name.startswith(led["prefix"] + "_")
        else:
            assert fn.name == s.fn_names[wt]
        doc = ast.get_docstring(fn)
        want_open = led.get("doc", "Compute.")
        assert doc and doc.split()[0].rstrip(".") == want_open.rstrip(".")
        for a in fn.args.args:
            if "hint" in led:
                assert getattr(a.annotation, "id", None) == led["hint"]
            else:
                assert a.annotation is None


def test_canonical_scores_fully_adherent_and_never_stale():
    for seed in range(13_400_000, 13_400_006):
        s, _ = _session_with_work(seed)
        for wt in s.work_turns:
            code = canonical_code(s, wt)
            wr = score_work(code, s, wt)
            assert wr.parse and wr.exec_ok, (seed, wt)
            for o in s.opportunities:
                if o.turn != wt:
                    continue
                e = wr.per_opportunity.get(o.opportunity_id, {})
                if o.cell == "active":
                    assert e.get("adherent") is True, (seed, wt, o.moment_class)
                if o.superseded:
                    assert not e.get("stale_action"), (seed, wt, o.moment_class)


def test_canonical_executes_all_ops():
    s, _ = _session_with_work(13_400_003)
    for wt in s.work_turns:
        op = s.ops[wt]
        assert op in OP_TESTS
        code = canonical_code(s, wt)
        x, y, want = OP_TESTS[op]
        ns = {}
        exec(code, ns)
        fn_name = next(k for k, v in ns.items() if callable(v) and not k.startswith("__"))
        assert ns[fn_name](x, y) == want


def test_deterministic():
    s, wt = _session_with_work(13_400_004)
    assert canonical_code(s, wt) == canonical_code(s, wt)
