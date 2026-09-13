"""The supersession structure the contract-state analysis labels sessions by.

Astra's back-on-track review (2026-09-13) found that
results/a-screen/analysis/stale2.py called request 1 "no supersession yet" for
every session.  That is false for reinstatement sessions: their authored prefix
supersedes the first rule before either live request.  The corrected analysis
keys its populations on `alt_was_in_force(session, k)`, and that function's
whole basis is the equivalence asserted here, so it is tested over the complete
pools rather than assumed.
"""

from stencil.a_screen_pool import screen_sessions
from stencil.a_train_pool import train_sessions


def _all_sessions():
    return list(screen_sessions()) + list(train_sessions())


def test_reinstatement_is_exactly_the_three_rule_turn_sessions():
    """Three rule turns <=> a supersession inside the prefix <=> reinstatement."""
    sessions = _all_sessions()
    assert len(sessions) == 624, len(sessions)
    for s in sessions:
        assert (len(s.rule_turns) == 3) == (s.lifecycle == "reinstatement"), (
            f"{s.id}: lifecycle {s.lifecycle} with rule turns {s.rule_turns}"
        )
        assert len(s.rule_turns) in (2, 3), f"{s.id}: {s.rule_turns}"


def test_reinstatement_request_1_alternative_is_the_superseded_rule():
    """At request 1 of a reinstatement, the alternative state is the rule the
    prefix already replaced -- so following it IS a stale-convention error."""
    for s in _all_sessions():
        if s.lifecycle != "reinstatement":
            continue
        # turn 10 states states[0]; turn 12 replaces it with states[1].
        assert s.state_at[0] == s.states[1], (s.id, s.states, s.state_at)
        assert s.other(s.state_at[0]) == s.states[0], (s.id, s.states, s.state_at)
        # the event reinstates the original for request 2
        assert s.state_at[1] == s.states[0], (s.id, s.states, s.state_at)


def test_non_reinstatement_request_1_alternative_was_never_in_force():
    """Everywhere else the prefix states one rule only, so at request 1 the
    alternative has no history and must not be scored as stale."""
    for s in _all_sessions():
        if s.lifecycle == "reinstatement":
            continue
        assert s.state_at[0] == s.states[0], (s.id, s.states, s.state_at)
        assert len(s.rule_turns) == 2, (s.id, s.rule_turns)


def test_request_2_alternative_is_request_1s_state_exactly_when_changed():
    """The request-2 population key: the alternative at request 2 is the state
    that was in force at request 1, and it is superseded iff the event changed
    the convention."""
    for s in _all_sessions():
        changed = s.state_at[0] != s.state_at[1]
        assert changed == (s.lifecycle != "stable"), (s.id, s.lifecycle)
        if changed:
            assert s.other(s.state_at[1]) == s.state_at[0], (s.id, s.state_at)
