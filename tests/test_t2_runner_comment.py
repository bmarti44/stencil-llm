"""Exp 0 instrument fix: the comment checker must see a trailing '# reviewed' line.

Before 2026-09-11 ``score_work`` used ``ast.get_source_segment``, whose segment ends
at the function's last statement, so the canonical adherent program from
``wave_ref.canonical_code`` (comment after the return) always scored non-adherent.
"""

from stencil.t2_runner import score_work, score_work_multi
from stencil.t2_sessions import generate_t2
from stencil.wave_ref import canonical_code


def _comment_session():
    for seed in range(13_690_000, 13_690_200):
        sess = generate_t2(seed, 20, "final", interference="s0")
        for wt in sess.work_turns:
            if "comment" in sess.ledger_at[wt] and any(
                o.turn == wt and o.moment_class == "comment" and o.cell == "active"
                for o in sess.opportunities
            ):
                return sess, wt
    raise AssertionError("no comment-governed work turn found in the smoke seed block")


def _comment_entry(result, sess, wt):
    for o in sess.opportunities:
        if o.turn == wt and o.moment_class == "comment":
            return result.per_opportunity[o.opportunity_id]
    raise AssertionError("no comment opportunity")


def test_canonical_program_is_comment_adherent():
    sess, wt = _comment_session()
    code = canonical_code(sess, wt)
    assert code.rstrip().endswith("# reviewed")
    result = score_work(code, sess, wt)
    assert result.parse and result.exec_ok
    entry = _comment_entry(result, sess, wt)
    assert entry["value_used"] == "# reviewed" and entry["adherent"] is True


def test_program_without_trailing_comment_is_not_adherent():
    sess, wt = _comment_session()
    code = canonical_code(sess, wt).replace("\n    # reviewed", "")
    entry = _comment_entry(score_work(code, sess, wt), sess, wt)
    assert entry["value_used"] is None and entry["adherent"] is False


def test_comment_before_last_statement_does_not_count():
    sess, wt = _comment_session()
    code = canonical_code(sess, wt)
    lines = code.rstrip().split("\n")
    # move the comment above the return: it is no longer the LAST line of the body
    lines.insert(-2, "    # reviewed")
    lines = lines[:-1]
    entry = _comment_entry(score_work("\n".join(lines) + "\n", sess, wt), sess, wt)
    assert entry["value_used"] is None


def test_trailing_comment_then_next_top_level_statement():
    sess, wt = _comment_session()
    code = canonical_code(sess, wt) + "\nX = 1\n"
    entry = _comment_entry(score_work(code, sess, wt), sess, wt)
    assert entry["value_used"] == "# reviewed"


def test_score_work_multi_uses_three_inputs():
    sess, wt = _comment_session()
    good = canonical_code(sess, wt)
    assert score_work_multi(good, sess, wt).exec_ok
    # a program that only passes the single registered input pair
    from stencil.t2_runner import OP_TESTS

    x, y, want = OP_TESTS[sess.ops[wt]]
    name = good.split("(")[0].replace("def ", "")
    cheat = f"def {name}(a, b):\n    return {want} if (a, b) == ({x}, {y}) else None\n"
    assert score_work(cheat, sess, wt).exec_ok
    assert not score_work_multi(cheat, sess, wt).exec_ok
