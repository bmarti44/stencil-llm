# ruff: noqa: E501
"""S16: coupon codes — naming (target, reinstatement) x logging (support, warn)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '"""couponbook package."""\n'

_MODEL = '''"""Coupon records."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Coupon:
    code: str
    percent_off: int
    status: str = "active"
'''

_BOOK_HEAD = '''"""In-memory coupon book."""

import logging
{extra_imports}
from couponbook.model import Coupon

log = logging.getLogger(__name__)


class CouponBook:
    def __init__(self) -> None:
        self._coupons: dict[str, Coupon] = {{}}

    def issue_coupon(self, code: str, percent_off: int) -> Coupon:
        coupon = Coupon(code=code.upper(), percent_off=percent_off)
        self._coupons[coupon.code] = coupon
        return coupon

    def find(self, code: str) -> Coupon | None:
        return self._coupons.get(code.upper())

    def count(self) -> int:
        return len(self._coupons)
'''

_BOOK = _BOOK_HEAD.format(extra_imports="")

_FILES = {
    "couponbook/__init__.py": _INIT,
    "couponbook/model.py": _MODEL,
    "couponbook/book.py": _BOOK,
}

# ----------------------------------------------------------------- checkpoint 1: redeem

_C1_HELPER = """import logging

from couponbook.book import CouponBook


def _redeem(book):
    fn = getattr(book, "coupon_redeem", None) or getattr(book, "redeem_coupon", None)
    assert fn is not None, "no redeem method found"
    return fn
"""

_C1_FUNCTIONAL = {
    "test_redeem_functional.py": _C1_HELPER
    + """

def test_redeem_sets_status_and_stores():
    b = CouponBook()
    c = b.issue_coupon("SPRING10", 10)
    out = _redeem(b)(c.code)
    assert out.status == "redeemed"
    assert b.find("SPRING10").status == "redeemed"


def test_redeem_is_case_insensitive_and_keeps_fields():
    b = CouponBook()
    b.issue_coupon("welcome5", 5)
    out = _redeem(b)("Welcome5")
    assert out.code == "WELCOME5" and out.percent_off == 5


def test_redeem_twice_is_noop():
    b = CouponBook()
    c = b.issue_coupon("SPRING10", 10)
    first = _redeem(b)(c.code)
    out = _redeem(b)(c.code)
    assert out == first and b.find(c.code) == first


def test_redeem_unknown_raises_keyerror():
    b = CouponBook()
    try:
        _redeem(b)("NOPE")
    except KeyError:
        return
    raise AssertionError("expected KeyError for an unknown code")
"""
}

_C1_REGRESSION = {
    "test_redeem_regression.py": """from couponbook.book import CouponBook


def test_issue_find_count_unchanged():
    b = CouponBook()
    c = b.issue_coupon("spring10", 10)
    assert c.code == "SPRING10" and c.status == "active" and c.percent_off == 10
    assert b.find("Spring10") is c
    assert b.find("OTHER") is None
    assert b.count() == 1
"""
}

_C1_CONTRACT = {
    "verb_noun": {
        "test_redeem_naming.py": """from couponbook.book import CouponBook


def test_redeem_is_verb_noun():
    assert hasattr(CouponBook, "redeem_coupon")
    assert not hasattr(CouponBook, "coupon_redeem")
"""
    },
    "noun_verb": {
        "test_redeem_naming.py": """from couponbook.book import CouponBook


def test_redeem_is_noun_verb():
    assert hasattr(CouponBook, "coupon_redeem")
    assert not hasattr(CouponBook, "redeem_coupon")
"""
    },
}

_C1_SUPPORT = {
    "test_redeem_logging.py": _C1_HELPER
    + """

def test_redeeming_redeemed_coupon_warns_exactly_once(caplog):
    b = CouponBook()
    c = b.issue_coupon("SPRING10", 10)
    _redeem(b)(c.code)
    with caplog.at_level(logging.DEBUG):
        _redeem(b)(c.code)
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1, [r.getMessage() for r in caplog.records]
"""
}


def _gold1(name: str) -> str:
    return (
        _BOOK_HEAD.format(extra_imports="from dataclasses import replace\n").rstrip(
            "\n"
        )
        + f"""

    def {name}(self, code: str) -> Coupon:
        coupon = self._coupons[code.upper()]
        if coupon.status == "redeemed":
            log.warning("coupon %s was already redeemed", coupon.code)
            return coupon
        redeemed = replace(coupon, status="redeemed")
        self._coupons[coupon.code] = redeemed
        return redeemed
"""
    )


_REQ1 = Request(
    text=(
        "Add a public method on CouponBook that redeems a coupon: it takes the code "
        "(matched case-insensitively like find), stores the coupon with status "
        '"redeemed" and returns it. An unknown code raises KeyError. Redeeming a coupon '
        "that is already redeemed is the notable no-op case: nothing changes and the "
        "coupon is returned as is."
    ),
    target="couponbook/book.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold={"verb_noun": _gold1("redeem_coupon"), "noun_verb": _gold1("coupon_redeem")},
)

# ----------------------------------------------------------------- checkpoint 2: revoke

_C2_HELPER = """import logging

from couponbook.book import CouponBook


def _revoke(book):
    fn = getattr(book, "revoke_coupon", None) or getattr(book, "coupon_revoke", None)
    assert fn is not None, "no revoke method found"
    return fn
"""

_C2_FUNCTIONAL = {
    "test_revoke_functional.py": _C2_HELPER
    + """

def test_revoke_sets_status_and_stores():
    b = CouponBook()
    c = b.issue_coupon("SPRING10", 10)
    out = _revoke(b)(c.code)
    assert out.status == "revoked"
    assert b.find("SPRING10").status == "revoked"


def test_revoke_is_case_insensitive_and_keeps_fields():
    b = CouponBook()
    b.issue_coupon("welcome5", 5)
    out = _revoke(b)("welcome5")
    assert out.code == "WELCOME5" and out.percent_off == 5


def test_revoke_twice_is_noop():
    b = CouponBook()
    c = b.issue_coupon("SPRING10", 10)
    first = _revoke(b)(c.code)
    out = _revoke(b)(c.code)
    assert out == first and b.find(c.code) == first


def test_revoke_unknown_raises_keyerror():
    b = CouponBook()
    try:
        _revoke(b)("NOPE")
    except KeyError:
        return
    raise AssertionError("expected KeyError for an unknown code")
"""
}

_C2_REGRESSION = {
    "test_revoke_regression.py": """from couponbook.book import CouponBook


def _redeem(book):
    return getattr(book, "coupon_redeem", None) or getattr(book, "redeem_coupon", None)


def test_issue_find_count_redeem_unchanged():
    b = CouponBook()
    c = b.issue_coupon("spring10", 10)
    assert b.find("SPRING10") is c and b.count() == 1
    assert _redeem(b)("spring10").status == "redeemed"
"""
}

_C2_CONTRACT = {
    "verb_noun": {
        "test_revoke_naming.py": """from couponbook.book import CouponBook


def test_revoke_is_verb_noun():
    assert hasattr(CouponBook, "revoke_coupon")
    assert not hasattr(CouponBook, "coupon_revoke")
"""
    },
    "noun_verb": {
        "test_revoke_naming.py": """from couponbook.book import CouponBook


def test_revoke_is_noun_verb():
    assert hasattr(CouponBook, "coupon_revoke")
    assert not hasattr(CouponBook, "revoke_coupon")
"""
    },
}

_C2_SUPPORT = {
    "test_revoke_logging.py": _C2_HELPER
    + """

def test_revoking_revoked_coupon_warns_exactly_once(caplog):
    b = CouponBook()
    c = b.issue_coupon("SPRING10", 10)
    _revoke(b)(c.code)
    with caplog.at_level(logging.DEBUG):
        _revoke(b)(c.code)
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1, [r.getMessage() for r in caplog.records]
"""
}


def _gold2(name: str) -> str:
    # Built on the checkpoint-1 gold under the state then in force (noun_verb).
    return (
        _gold1("coupon_redeem").rstrip("\n")
        + f"""

    def {name}(self, code: str) -> Coupon:
        coupon = self._coupons[code.upper()]
        if coupon.status == "revoked":
            log.warning("coupon %s was already revoked", coupon.code)
            return coupon
        revoked = replace(coupon, status="revoked")
        self._coupons[coupon.code] = revoked
        return revoked
"""
    )


_REQ2 = Request(
    text=(
        "Add a public method on CouponBook that revokes a coupon: it takes the code "
        '(matched case-insensitively like find), stores the coupon with status "revoked" '
        "and returns it. An unknown code raises KeyError. Revoking a coupon that is "
        "already revoked is the notable no-op case: nothing changes and the coupon is "
        "returned as is."
    ),
    target="couponbook/book.py",
    functional_tests=_C2_FUNCTIONAL,
    regression_tests=_C2_REGRESSION,
    contract_tests=_C2_CONTRACT,
    support_tests=_C2_SUPPORT,
    gold={"verb_noun": _gold2("revoke_coupon"), "noun_verb": _gold2("coupon_revoke")},
)

# ----------------------------------------------------------------- prefix (16 turns)

_PREFIX = [
    Turn(
        "user",
        "I run the web shop for a small pottery studio and we hand out discount codes at "
        "markets: SPRING10, WELCOME5, that sort of thing, printed on little cards. Right "
        "now the codes live in a text file that the checkout script greps, and twice now "
        "a code has been used after we meant to stop it. I want a small package, "
        "couponbook, that holds the codes in memory for the checkout process: issue a "
        "code with a percentage off, look it up, and later mark it used or pulled. One "
        "process, one shop, a few dozen codes a season. The checkout script is a Flask "
        "app but the package itself should know nothing about HTTP. Here is the README "
        "draft:\n\n```\n# couponbook\n\nIn-memory coupon codes for a single shop "
        "process. A coupon is a code (case-insensitive, stored upper-case), a whole-"
        "number percentage off and a status. Codes are issued by the studio, redeemed "
        "once at checkout, and can be pulled early.\n```\n\nIs 'percentage off' as an int "
        "too restrictive? We have never done a fractional discount and I would rather "
        "not deal with Decimal.",
    ),
    Turn(
        "assistant",
        "An int percentage is the right call for what you describe: every code you "
        "have ever printed is a whole number, ints compare and serialise without "
        "surprises, and if a 12.5 percent code ever appears you can widen the type in "
        "one place. The README is clear; I would add the load/save story and the "
        "non-goals so the Flask side knows where the boundary is:\n\n```\n## Persistence\n"
        "The library does no I/O. The checkout app loads `coupons.json` at start-up "
        "into a `CouponBook` and writes it back after each change.\n\n## Non-goals\n- "
        "expiry dates\n- per-customer limits\n- fixed-amount discounts\n```\n\nKeeping "
        "I/O out of the class also keeps the tests tiny:\n\n```python\ndef "
        "test_issue_upper_cases_code():\n    book = CouponBook()\n    assert book.issue_"
        'coupon("spring10", 10).code == "SPRING10"\n```\n\nThe case-insensitive rule '
        "is worth stating in the docstring of every method that takes a code, because "
        "it is the kind of thing a future maintainer will otherwise re-implement.",
    ),
    Turn(
        "user",
        "Here is the model and the current tests. Coupon is a frozen dataclass with "
        'code, percent_off and status, and status starts at "active". I expect '
        '"redeemed" and "revoked" as the other two values: redeemed when a customer '
        "uses it at checkout, revoked when we pull a code early because a card batch "
        "was misprinted or a market was cancelled.\n\n```python\nfrom couponbook.book "
        "import CouponBook\n\n\ndef test_issue_upper_cases_code():\n    b = CouponBook()\n"
        '    assert b.issue_coupon("spring10", 10).code == "SPRING10"\n\n\ndef '
        "test_find_is_case_insensitive():\n    b = CouponBook()\n    c = b.issue_coupon("
        '"WELCOME5", 5)\n    assert b.find("welcome5") is c\n\n\ndef '
        'test_find_missing_returns_none():\n    assert CouponBook().find("NOPE") is None\n'
        "```\n\nShould the two end states be one field, or should I have two booleans, "
        "redeemed and revoked? The checkout only cares whether a code is usable, and the "
        "studio side cares about the distinction only when we reconcile the season: how "
        "many cards came back versus how many we pulled.",
    ),
    Turn(
        "assistant",
        "One status field. Two booleans create a fourth combination (redeemed and "
        "revoked at once) that means nothing and that every reader has to reason about. "
        "A single `status` with three values reads directly off the record and the "
        'checkout question becomes `coupon.status == "active"`. Each state change is a '
        "CouponBook method that looks the coupon up, builds the new record with "
        "`dataclasses.replace` and stores it under the same code:\n\n```python\ncoupon "
        '= self._coupons[code.upper()]\nupdated = replace(coupon, status="redeemed")\n'
        "self._coupons[coupon.code] = updated\nreturn updated\n```\n\nFrozen records "
        "mean the Flask request that holds an old Coupon cannot mutate the book behind "
        "your back, which is the bug the grep-a-text-file approach had in a different "
        "costume. Your tests are good; I would add one for `count()` so the JSON loader "
        "has something to assert against:\n\n```python\ndef test_count_after_two_issues():"
        '\n    b = CouponBook()\n    b.issue_coupon("a1", 5)\n    b.issue_coupon("b2", '
        "10)\n    assert b.count() == 2\n```",
    ),
    Turn(
        "user",
        "Done, count test added. Next question: when the checkout asks about a code that "
        "does not exist, `find` returns None and the app shows 'code not recognised'. "
        "That is right. But what about the action methods we are about to add? If a "
        "cashier types a code that is not in the book and we try to redeem it, should "
        "that also be None, or an exception? Here is what happened in the old script "
        "when a misspelt code was marked used:\n\n```\n$ python mark_used.py SPRNG10\n"
        "marked SPRNG10 as used\n$ grep SPRNG10 codes.txt\n$\n```\n\nIt printed success "
        "and changed nothing, and nobody noticed for a week. I never want that again. "
        "The same script also accepted lower-case input and then failed to match the "
        "upper-case file, which is why `find` now upper-cases before the lookup; the "
        "action methods should do the same so a cashier can type the code any way.",
    ),
    Turn(
        "assistant",
        "Make the actions raise KeyError. `find` is a lookup and None is the honest "
        "answer to 'is this code known'; redeeming or revoking is an action on a coupon "
        "that must exist, and acting on a missing one is a caller error that should stop "
        "the program loudly rather than print success. So the rule is: lookups return "
        "None, actions raise KeyError. The Flask handler turns the KeyError into a 404 "
        "or a friendly message in one place:\n\n```python\ntry:\n    coupon = "
        'book.redeem_coupon(code)\nexcept KeyError:\n    abort(404, f"unknown code '
        '{code}")\n```\n\nIndexing the dict directly (`self._coupons[code.upper()]`) '
        "gives you the KeyError for free and the message carries the code. Your "
        "SPRNG10 story is exactly the failure mode this prevents: the script would have "
        "died with `KeyError: 'SPRNG10'` on the first run. Upper-casing inside each "
        "action, the way `find` does, keeps the case rule in the book rather than in "
        "every caller, so the Flask handler can pass the form field through untouched.",
    ),
    Turn(
        "user",
        "Agreed. Related: what should happen when someone redeems a code that was "
        "already redeemed? The checkout will legitimately see this when a customer "
        "tries a card twice, and it is not an error in the sense that the program did "
        "something wrong, but I want it to be visible somewhere because a pattern of "
        "them means a card got photocopied. At the same time I do not want the library "
        "printing to the terminal; the Flask logs are already noisy enough. Here is a "
        "sample of the access log for context:\n\n```\n127.0.0.1 - - [14/Sep/2026 "
        '10:02:11] "POST /checkout/apply HTTP/1.1" 200 -\n127.0.0.1 - - [14/Sep/2026 '
        '10:02:19] "POST /checkout/apply HTTP/1.1" 200 -\n```\n\nWhat is the idiomatic '
        "way for a library to flag this kind of thing?",
    ),
    Turn(
        "assistant",
        "The idiom is the `logging` module with a module logger: `log = "
        "logging.getLogger(__name__)` at the top of the module, and `log.warning(...)` "
        "for conditions that are legal but worth a human's attention. The library never "
        "configures handlers or levels; the Flask app decides where the records go, and "
        "because the logger is named `couponbook.book` the app can route just those "
        'lines to a file:\n\n```python\nhandler = logging.FileHandler("coupon-'
        'warnings.log")\nlogging.getLogger("couponbook").addHandler(handler)\n```\n\n'
        "A double redemption then shows up as one line, `WARNING couponbook.book: coupon "
        "SPRING10 was already redeemed`, which is exactly the trail you want for "
        "spotting photocopied cards, and the method still returns the coupon unchanged "
        "so the checkout can say 'already used'. Tests assert on it with pytest's "
        "`caplog` fixture, which captures every record the library emits:\n\n```python\n"
        "def test_double_redeem_warns(caplog):\n    with caplog.at_level(logging.DEBUG):\n"
        "        ...  # the second redemption\n    assert [r.levelname for r in "
        'caplog.records] == ["WARNING"]\n```',
    ),
    Turn(
        "user",
        "Let's fix that as a convention: when a CouponBook method hits a notable but "
        "harmless condition (the request being a no-op, like redeeming an already "
        "redeemed code), it emits exactly one logging.warning through the module "
        "logger. Not two, not a warning plus an info, nothing at debug level. The "
        "normal path logs nothing.",
    ),
    Turn(
        "assistant",
        "Noted: exactly one `log.warning` via `logging.getLogger(__name__)` for the "
        "notable no-op conditions, no other record of any level, and silence on the "
        "normal path. I will include the coupon code in the message so each line is "
        "useful on its own.",
    ),
    Turn(
        "user",
        "Naming: public CouponBook methods are verb_noun, like issue_coupon. New public "
        "methods follow that pattern so the class reads as a list of things you can do "
        "with a coupon.",
    ),
    Turn(
        "assistant",
        "Understood: verb_noun for public CouponBook methods, matching issue_coupon. A "
        "method that redeems a coupon would be redeem_coupon, and private helpers can be "
        "named freely since they are not part of the API. I will also keep the "
        "case-insensitive rule in each new method's docstring as discussed.",
    ),
    Turn(
        "user",
        "Actually, change of plan on naming. My co-owner, who writes most of the Flask "
        "side, wants noun_verb for everything coupon-related so the methods group under "
        "'coupon' in autocomplete. So effective now: new public CouponBook methods are "
        "named noun_verb (coupon_redeem style). Existing names stay; only new methods "
        "follow the new pattern.",
    ),
    Turn(
        "assistant",
        "Understood: from now on new public CouponBook methods are noun_verb, for "
        "example coupon_redeem, while issue_coupon and find keep their current names. I "
        "will follow the new pattern for anything new, and nothing else about the "
        "conventions we fixed (logging, KeyError on unknown codes) changes.",
    ),
    Turn(
        "user",
        "Good. Let's get the first real method in; the autumn market is this weekend and "
        "the cards are printed. I will paste the current files with every request so you "
        "always see the real state rather than my memory of it.",
    ),
    Turn(
        "assistant",
        "Ready. Send the request with the files and I will return the complete book "
        "module, keeping issue_coupon, find and count exactly as they are.",
    ),
]

_EVENT = (
    "Reverting the naming change: my co-owner and I talked it through and we are going "
    "back to verb_noun for new public CouponBook methods (revoke_coupon style), matching "
    "issue_coupon. The noun_verb rule is withdrawn; existing method names, including the "
    "one you just added, stay exactly as they are."
)


def build() -> Session:
    return Session(
        id="S16",
        project="couponbook",
        target_family="naming",
        support_family="logging",
        lifecycle="reinstatement",
        files=_FILES,
        prefix=_PREFIX,
        states=("verb_noun", "noun_verb"),
        state_at=("noun_verb", "verb_noun"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10, 12),
    )
