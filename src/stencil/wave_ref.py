# ruff: noqa: E501
"""W0.0 canonical reference builder (INTERNAL-WAVE-PLAN v3, frozen).

Deterministic map (session, work turn) -> canonical adherent code.
Name {prefix}_{fn} (bare {fn} when prefix inactive); docstring always
present, opening with the ledger doc value when active else the neutral
opener "Compute."; args typed with the hint value when active; body
implements sess.ops[wt] per OP_TESTS semantics.
"""

_BODIES = {
    "sum": "return a + b",
    "max": "return a if a > b else b",
    "mul": "return a * b",
    "sub": "return a - b",
}


def canonical_code(sess, wt: int) -> str:
    led = sess.ledger_at[wt]
    fn = sess.fn_names[wt]
    name = f"{led['prefix']}_{fn}" if "prefix" in led else fn
    ann = f": {led['hint']}" if "hint" in led else ""
    opener = led.get("doc", "Compute")
    # the scorer compares the docstring's FIRST WORD to the pool value —
    # the opener token must appear unmodified
    doc = f'"""{opener} the result."""'
    body = _BODIES[sess.ops[wt]]
    tail = "\n    # reviewed" if "comment" in led else ""
    return f"def {name}(a{ann}, b{ann}):\n    {doc}\n    {body}{tail}\n"
