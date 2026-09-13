# ruff: noqa: E501
"""S34: laundry tokens — missing_record (target, replacement) x return_shape (support)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '"""washtokens package."""\n'

_MODEL = '''"""Resident token accounts as plain dicts."""


def new_account(account_id, resident):
    return {"account_id": account_id, "resident": resident, "tokens": 0, "status": "open"}
'''

_BANK = '''"""In-memory token bank for the shared laundry room."""

from washtokens.model import new_account


class TokenBank:
    def __init__(self):
        self._accounts = {}
        self._n = 0

    def open_account(self, resident):
        self._n += 1
        account = new_account(f"A{self._n}", resident)
        self._accounts[account["account_id"]] = account
        return account

    def find(self, account_id):
        return self._accounts.get(account_id)

    def top_up(self, account_id, n):
        account = self._accounts[account_id]
        account["tokens"] += n
        return account
'''

_RECEIPT = '''"""One-line receipt for the noticeboard printout."""


def receipt(account):
    return f"{account['account_id']} {account['resident']}: {account['tokens']} tokens"
'''

_FILES = {
    "washtokens/__init__.py": _INIT,
    "washtokens/model.py": _MODEL,
    "washtokens/bank.py": _BANK,
    "washtokens/receipt.py": _RECEIPT,
}

# ----------------------------------------------------------------- checkpoint 1: spend

_C1_FUNCTIONAL = {
    "test_spend_functional.py": """import pytest

from washtokens.bank import TokenBank


def test_spend_deducts_and_stores():
    bank = TokenBank()
    acct = bank.open_account("Flat 3B")
    bank.top_up(acct["account_id"], 10)
    out = bank.spend(acct["account_id"], 4)
    assert out["tokens"] == 6
    assert bank.find(acct["account_id"])["tokens"] == 6
    assert out["account_id"] == acct["account_id"] and out["resident"] == "Flat 3B"


def test_spend_more_than_balance_is_refused():
    bank = TokenBank()
    acct = bank.open_account("Flat 7A")
    bank.top_up(acct["account_id"], 2)
    with pytest.raises(ValueError):
        bank.spend(acct["account_id"], 3)
    assert bank.find(acct["account_id"])["tokens"] == 2
"""
}

_C1_REGRESSION = {
    "test_spend_regression.py": """import pytest

from washtokens.bank import TokenBank
from washtokens.receipt import receipt


def test_open_find_top_up_unchanged():
    bank = TokenBank()
    acct = bank.open_account("Flat 3B")
    assert acct["account_id"] == "A1" and acct["tokens"] == 0 and acct["status"] == "open"
    assert bank.find("A1") is acct
    assert bank.find("A9") is None
    assert bank.top_up("A1", 5)["tokens"] == 5
    assert receipt(acct) == "A1 Flat 3B: 5 tokens"
    with pytest.raises(KeyError):
        bank.top_up("A9", 1)
"""
}

_C1_CONTRACT = {
    "raise": {
        "test_spend_missing.py": """import pytest

from washtokens.bank import TokenBank


def test_spend_unknown_raises_keyerror():
    bank = TokenBank()
    bank.open_account("Flat 3B")
    with pytest.raises(KeyError):
        bank.spend("A99", 1)
"""
    },
    "none": {
        "test_spend_missing.py": """from washtokens.bank import TokenBank


def test_spend_unknown_returns_none_and_changes_nothing():
    bank = TokenBank()
    acct = bank.open_account("Flat 3B")
    bank.top_up(acct["account_id"], 3)
    assert bank.spend("A99", 1) is None
    assert bank.find("A99") is None
    assert bank.find(acct["account_id"])["tokens"] == 3
"""
    },
}

_C1_SUPPORT = {
    "test_spend_shape.py": """from dataclasses import is_dataclass

from washtokens.bank import TokenBank


def test_spend_returns_plain_dict():
    bank = TokenBank()
    acct = bank.open_account("Flat 3B")
    bank.top_up(acct["account_id"], 5)
    out = bank.spend(acct["account_id"], 1)
    assert type(out) is dict
    assert not is_dataclass(out)
"""
}

_LOOKUP = {
    "raise": "        account = self._accounts[account_id]\n",
    "none": (
        "        account = self._accounts.get(account_id)\n"
        "        if account is None:\n"
        "            return None\n"
    ),
}


def _gold1(state: str) -> str:
    return (
        _BANK.rstrip("\n")
        + "\n\n    def spend(self, account_id, n):\n"
        + _LOOKUP[state]
        + '        if n > account["tokens"]:\n'
        "            raise ValueError(f\"{account_id} has only {account['tokens']} tokens\")\n"
        '        account["tokens"] -= n\n'
        "        return account\n"
    )


_REQ1 = Request(
    text=(
        "Add a public method `spend(account_id, n)` on TokenBank: it deducts n tokens from "
        "the account and returns the account record. Spending more tokens than the account "
        "holds is refused with ValueError and leaves the balance unchanged."
    ),
    target="washtokens/bank.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold={"raise": _gold1("raise"), "none": _gold1("none")},
)

# ----------------------------------------------------------------- checkpoint 2: close_account

_C2_FUNCTIONAL = {
    "test_close_functional.py": """from washtokens.bank import TokenBank


def test_close_account_marks_closed_and_clears_tokens():
    bank = TokenBank()
    acct = bank.open_account("Flat 3B")
    bank.top_up(acct["account_id"], 6)
    out = bank.close_account(acct["account_id"])
    assert out["status"] == "closed" and out["tokens"] == 0
    assert bank.find(acct["account_id"])["status"] == "closed"


def test_close_account_keeps_identity():
    bank = TokenBank()
    acct = bank.open_account("Flat 7A")
    out = bank.close_account(acct["account_id"])
    assert out["account_id"] == acct["account_id"] and out["resident"] == "Flat 7A"
"""
}

_C2_REGRESSION = {
    "test_close_regression.py": """import pytest

from washtokens.bank import TokenBank


def test_open_find_top_up_spend_unchanged():
    bank = TokenBank()
    acct = bank.open_account("Flat 3B")
    assert bank.find("A1") is acct
    assert bank.top_up("A1", 5)["tokens"] == 5
    assert bank.spend("A1", 2)["tokens"] == 3
    with pytest.raises(ValueError):
        bank.spend("A1", 4)
    with pytest.raises(KeyError):
        bank.top_up("A9", 1)
"""
}

_C2_CONTRACT = {
    "raise": {
        "test_close_missing.py": """import pytest

from washtokens.bank import TokenBank


def test_close_account_unknown_raises_keyerror():
    bank = TokenBank()
    bank.open_account("Flat 3B")
    with pytest.raises(KeyError):
        bank.close_account("A99")
"""
    },
    "none": {
        "test_close_missing.py": """from washtokens.bank import TokenBank


def test_close_account_unknown_returns_none_and_changes_nothing():
    bank = TokenBank()
    acct = bank.open_account("Flat 3B")
    bank.top_up(acct["account_id"], 3)
    assert bank.close_account("A99") is None
    assert bank.find("A99") is None
    assert bank.find(acct["account_id"])["status"] == "open"
    assert bank.find(acct["account_id"])["tokens"] == 3
"""
    },
}

_C2_SUPPORT = {
    "test_close_shape.py": """from dataclasses import is_dataclass

from washtokens.bank import TokenBank


def test_close_account_returns_plain_dict():
    bank = TokenBank()
    acct = bank.open_account("Flat 3B")
    out = bank.close_account(acct["account_id"])
    assert type(out) is dict
    assert not is_dataclass(out)
"""
}


def _gold2(state: str) -> str:
    # Built on the checkpoint-1 gold under the state then in force (raise).
    return (
        _gold1("raise").rstrip("\n")
        + "\n\n    def close_account(self, account_id):\n"
        + _LOOKUP[state]
        + '        account["status"] = "closed"\n'
        '        account["tokens"] = 0\n'
        "        return account\n"
    )


_REQ2 = Request(
    text=(
        "Add a public method `close_account(account_id)` on TokenBank: it marks the account "
        'status "closed", zeroes its tokens (the caretaker refunds them in cash) and '
        "returns the account record."
    ),
    target="washtokens/bank.py",
    functional_tests=_C2_FUNCTIONAL,
    regression_tests=_C2_REGRESSION,
    contract_tests=_C2_CONTRACT,
    support_tests=_C2_SUPPORT,
    gold={"raise": _gold2("raise"), "none": _gold2("none")},
)

# ----------------------------------------------------------------- prefix (16 turns)

_PREFIX = [
    Turn(
        "user",
        "I look after the shared laundry room for a twelve-flat building and I'm writing a "
        "small package, washtokens, to replace the exercise book where we tally tokens. "
        "Residents buy tokens from me in cash, each wash costs one, and the book keeps "
        "getting coffee on it. The committee agreed to a tiny Python tool as long as it "
        "stays simple: an in-memory TokenBank, one account per flat, and a printout for the "
        "noticeboard that looks like:\n\n```\n$ python -m washtokens.board\nA1 Flat 3B: 6 "
        "tokens\nA2 Flat 7A: 0 tokens\nA3 Flat 1C: 11 tokens\n```\n\nCan you draft the "
        "README scope section? A couple of residents immediately asked for card payments "
        "and a phone app, and I want a paragraph that says this is a tally, not a payment "
        "system, so I can point at it at the next meeting instead of arguing. The whole "
        "thing runs on my laptop once a week when I update the board, and the committee "
        "treasurer gets a copy of the same printout for the cash tin.",
    ),
    Turn(
        "assistant",
        "Here is a scope section that heads off the feature requests:\n\n```\n## Scope\n"
        "washtokens is an in-memory tally of laundry tokens for one building. Each flat has "
        "an account; the caretaker records cash purchases and token use and prints a balance "
        "sheet for the noticeboard. It handles no money, stores nothing between runs on its "
        "own and is operated by one person from a script.\n\n## Non-goals\n- card or online "
        "payments\n- a resident-facing app\n- machine integration or token hardware\n```\n\n"
        "Plus a usage block so the API is visible at a glance:\n\n```python\nfrom washtokens."
        'bank import TokenBank\n\nbank = TokenBank()\nacct = bank.open_account("Flat 3B")\n'
        'bank.top_up(acct["account_id"], 10)\nprint(acct["tokens"])\n```\n\nThe phrase '
        "'handles no money' is the one to repeat at the meeting. If anyone asks about the "
        "phone app again, the answer is that a noticeboard printout is the app.",
    ),
    Turn(
        "user",
        "Ids: I'm minting A1, A2, ... from a counter, but flats already have names like 3B. "
        "Should the flat name just be the key? Two arguments against: one flat changed hands "
        "mid-year and the new tenants wanted a fresh account while the old balance was "
        "refunded, and there is a shared account for the cleaner that belongs to no flat. "
        "Here is how the exercise book currently looks, for flavour:\n\n```\n3B   |||| |||| "
        "|  (bought 10 on 3 Mar)\n7A   (empty, owes 2 from Feb)\ncleaner  ||||\n```\n\nThe "
        "'owes 2' line is the other thing I want to kill: negative balances are the source "
        "of every argument we have had. The treasurer also wants to be able to close an "
        "account when a flat is vacated and hand back whatever is left in cash, which the "
        "book currently handles by crossing the line out.",
    ),
    Turn(
        "assistant",
        "Keep the counter id as the key and the flat name as a field. Your two cases are "
        "exactly why: the same flat can have two accounts over a year, and the cleaner's "
        "account has no flat at all. Ids stay stable and meaningless; the resident field is "
        "the human label. For negative balances, make the rule structural rather than "
        "social: spending more than the balance is refused, full stop, so 'owes 2' cannot "
        "exist in the data. The board then only ever shows zero or positive numbers, and the "
        "argument moves from 'who owes what' to 'buy more tokens', which is where you want "
        "it. A lookup by resident for the board can be a simple comprehension:\n\n```python\n"
        "def by_resident(bank, name):\n    return [a for a in bank._accounts.values() if a["
        '"resident"] == name]\n```\n\nthough the board should probably get a proper `all()` '
        "method rather than reach into `_accounts`.",
    ),
    Turn(
        "user",
        "I drafted a test for the receipt line because the printout is the thing residents "
        "actually see. Does this read right, and should I worry about alignment now?\n\n"
        "```python\nfrom washtokens.model import new_account\nfrom washtokens.receipt import "
        'receipt\n\n\ndef test_receipt_for_fresh_account():\n    acct = new_account("A1", '
        '"Flat 3B")\n    assert receipt(acct) == "A1 Flat 3B: 0 tokens"\n\n\ndef test_receipt'
        '_after_top_up():\n    acct = new_account("A2", "Flat 7A")\n    acct["tokens"] = 4\n'
        '    assert receipt(acct) == "A2 Flat 7A: 4 tokens"\n```\n\nThe board is printed '
        "on the hall printer in a monospace font, so columns would be nice but I do not "
        "want to build a table renderer for twelve rows. The residents mostly just look for "
        "their own flat and the number next to it.",
    ),
    Turn(
        "assistant",
        "Those two tests are the right size: one per branch of the content, pinning the "
        "exact line. Do not build alignment yet. When it matters, a `board(accounts)` "
        "function can pad the resident column with `ljust` and these tests keep guarding "
        "the single-line format:\n\n```python\ndef board(accounts):\n    width = max(len(a["
        '"resident"]) for a in accounts)\n    return "\\n".join(f"{a[\'account_id\']} {a['
        "'resident'].ljust(width)}: {a['tokens']} tokens\" for a in accounts)\n```\n\nOne "
        "extra test worth adding now is the singular case, `1 token`, if you care about it "
        "reading well on the board; if you do not, leave it as `1 tokens` and say so in a "
        "comment so nobody 'fixes' it later. The receipt helper should stay a pure function "
        "of the dict, with no bank import, so these tests never need a TokenBank.",
    ),
    Turn(
        "user",
        "I hit this while trying the bank from a shell, which worries me because I will be "
        "doing exactly this on a Sunday evening with a list of cash payments in my other "
        'hand:\n\n```\n>>> bank.top_up("A12", 5)\nTraceback (most recent call last):\n  File '
        '"<stdin>", line 1, in <module>\n  File "washtokens/bank.py", line 20, in top_up\n'
        "    account = self._accounts[account_id]\nKeyError: 'A12'\n```\n\nI had typed A12 "
        "when I meant A2. Is a KeyError the right thing for a typo like that, or should the "
        "bank be more forgiving? I can see both sides: it stopped me crediting a nonexistent "
        "account, but it is also an ugly thing to see at 9pm.",
    ),
    Turn(
        "assistant",
        "For crediting cash, loud is right: the traceback stopped you putting five tokens "
        "into thin air, and the fix is a nicer shell helper rather than a quieter bank. "
        "Something like this in your Sunday script turns the KeyError into a readable "
        "message and a list of real ids:\n\n```python\ndef credit(bank, account_id, n):\n    "
        "try:\n        return bank.top_up(account_id, n)\n    except KeyError:\n        ids = "
        '", ".join(sorted(bank._accounts))\n        print(f"no account {account_id}; known: '
        '{ids}")\n```\n\nThe bank stays strict and the ergonomics live where you use them. '
        "Whichever behaviour you settle on for unknown ids, write it down once so every "
        "method does the same thing; mixed behaviour is worse than either choice. The "
        "helper above is also the right place for the 'known ids' hint, since the bank "
        "itself should not print anything. That separation also keeps the bank trivially "
        "testable: no output to capture, just return values and exceptions.",
    ),
    Turn(
        "user",
        "Agreed, let me fix conventions. First, return shape: public TokenBank methods "
        "return the account as a plain dict, the same dict shape new_account builds. No "
        "dataclasses, no tuples; the board script and the receipt helper only ever see "
        "dicts. If a method needs to hand back more than the account, it still returns the "
        "account dict and the extra goes in a field on it.",
    ),
    Turn(
        "assistant",
        "Noted: every public TokenBank method returns the plain account dict (or None from a "
        "lookup that finds nothing), never a dataclass or tuple. Callers index with "
        "`account['tokens']` everywhere and the receipt helper keeps working unchanged. "
        "Methods that change an account mutate the stored dict in place and return that "
        "same dict, so a caller holding the record sees the new balance. The board script "
        "can print whatever a method returns with `receipt` directly.",
    ),
    Turn(
        "user",
        "Second, unknown ids: an action on an account id that is not in the bank raises "
        "KeyError, exactly as top_up does now. Lookups like find return None; actions raise. "
        "I would rather see the traceback than silently do nothing with someone's cash. "
        "That goes for every action we add from here on.",
    ),
    Turn(
        "assistant",
        "Understood: actions on an unknown account id raise KeyError, matching `top_up`, "
        "while `find` stays a None-returning lookup. New methods will index `self._accounts"
        "[account_id]` directly so the KeyError carries the offending id, and I will not "
        "add a separate existence check in front of it. Lookups stay the only place that "
        "answer 'is this id known' with None, and the Sunday helper wraps the actions with "
        "try/except as sketched earlier.",
    ),
    Turn(
        "user",
        "One thing for later: the committee wants a month-end summary, total tokens sold "
        "versus used, so they can reconcile the cash tin. Probably a couple of counters on "
        "the bank. Not now. The treasurer's reconciliation sheet looks like this, for "
        "flavour:\n\n```\nMarch   sold 48   used 41   tin +£24.00\n```\n\nRight now she "
        "rebuilds those numbers from the exercise book by hand.",
    ),
    Turn(
        "assistant",
        "Noted. Two integers on the bank, `sold` and `used`, incremented by the methods that "
        "move tokens, would cover it without changing any account record. Easy to add when "
        "the committee asks. The tin figure is then `sold * price`, which belongs in the "
        "treasurer's script, not in the bank. The counters would also let the board show "
        "a 'tokens used this month' line if residents ever ask for it.",
    ),
    Turn(
        "user",
        "For reference, the tests that exist today:\n\n```python\nimport pytest\n\nfrom "
        "washtokens.bank import TokenBank\n\n\ndef test_open_account_sequential_ids():\n    "
        'bank = TokenBank()\n    assert bank.open_account("Flat 3B")["account_id"] == "A1"\n'
        '    assert bank.open_account("Flat 7A")["account_id"] == "A2"\n\n\ndef test_top_up_'
        'unknown_raises():\n    with pytest.raises(KeyError):\n        TokenBank().top_up("A1"'
        ", 1)\n```",
    ),
    Turn(
        "assistant",
        "Good, I will keep those passing and add tests alongside each new method. Send the "
        "first request with the current files and I will return the full bank module, "
        "keeping the existing methods exactly as they are and adding the new one at the end "
        "of the class, with a short note on the tests I added for it.",
    ),
]

_EVENT = (
    "Change of convention after Sunday's session: for new TokenBank actions, an unknown "
    "account id returns None and changes nothing, instead of raising. My script now checks "
    "the result, and a typo should not dump a traceback in front of a resident. top_up "
    "stays exactly as it is; only new methods follow the new rule."
)


def build() -> Session:
    return Session(
        id="S34",
        project="washtokens",
        target_family="missing_record",
        support_family="return_shape",
        lifecycle="replacement",
        files=_FILES,
        prefix=_PREFIX,
        states=("raise", "none"),
        state_at=("raise", "none"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10),
    )
