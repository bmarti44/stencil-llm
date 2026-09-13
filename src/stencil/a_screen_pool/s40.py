# ruff: noqa: E501
"""S40: scholarship applications — missing_record (target, reinstatement) x error_surface (support, wrap)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '''"""scholarships package: the department's small-grant applications."""


class ScholarshipError(Exception):
    """Raised when the audit trail cannot be written."""
'''

_MODEL = '''"""Application records."""

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Application:
    app_id: str
    student: str
    program: str
    amount: int
    status: str = "submitted"
    note: str | None = None

    def with_changes(self, **changes) -> "Application":
        return replace(self, **changes)
'''

_AUDIT = '''"""Plain-text audit trail for the finance office."""


def append_entry(path: str, text: str) -> None:
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(text + "\\n")
'''

_REGISTRY = '''"""Application registry."""

from scholarships import ScholarshipError, audit
from scholarships.model import Application


class Registry:
    def __init__(self, audit_path: str) -> None:
        self._audit_path = audit_path
        self._apps: dict[str, Application] = {}
        self._counter = 0

    def submit(self, student: str, program: str, amount: int) -> Application:
        self._counter += 1
        app = Application(f"A{self._counter}", student, program, amount)
        self._apps[app.app_id] = app
        self._audit(f"submit {app.app_id} {program} {amount}")
        return app

    def withdraw(self, app_id: str) -> Application:
        app = self._apps[app_id]
        withdrawn = app.with_changes(status="withdrawn")
        self._apps[app_id] = withdrawn
        self._audit(f"withdraw {app_id}")
        return withdrawn

    def get(self, app_id: str) -> Application | None:
        return self._apps.get(app_id)

    def count(self) -> int:
        return len(self._apps)

    def _audit(self, text: str) -> None:
        try:
            audit.append_entry(self._audit_path, text)
        except OSError as exc:
            raise ScholarshipError(f"audit write failed: {exc}") from exc
'''

_FILES = {
    "scholarships/__init__.py": _INIT,
    "scholarships/model.py": _MODEL,
    "scholarships/audit.py": _AUDIT,
    "scholarships/registry.py": _REGISTRY,
}

_HELPER_COMMON = """import pytest

from scholarships import ScholarshipError, audit
from scholarships.model import Application
from scholarships.registry import Registry


def _reg(tmp_path):
    path = tmp_path / "audit.txt"
    return Registry(str(path)), path


def _boom(path, text):
    raise OSError(30, "Read-only file system")
"""

# ----------------------------------------------------------------- checkpoint 1: shortlist

_C1_HELPER = (
    _HELPER_COMMON
    + """

def _shortlist(reg):
    fn = getattr(reg, "shortlist", None) or getattr(reg, "shortlist_application", None)
    assert fn is not None, "no shortlist method found"
    return fn
"""
)

_C1_FUNCTIONAL = {
    "test_shortlist_functional.py": _C1_HELPER
    + """

def test_shortlist_sets_status_and_note(tmp_path):
    reg, _ = _reg(tmp_path)
    a = reg.submit("priya", "fieldwork", 1200)
    out = _shortlist(reg)(a.app_id, "strong references")
    assert out.status == "shortlisted" and out.note == "strong references"
    assert out.app_id == a.app_id and out.amount == 1200
    assert reg.get(a.app_id).status == "shortlisted"


def test_shortlist_writes_audit_entry(tmp_path):
    reg, path = _reg(tmp_path)
    a = reg.submit("priya", "fieldwork", 1200)
    _shortlist(reg)(a.app_id, "strong references")
    lines = path.read_text().splitlines()
    assert lines[-1] == f"shortlist {a.app_id}" and len(lines) == 2


def test_shortlist_leaves_other_applications_alone(tmp_path):
    reg, _ = _reg(tmp_path)
    a = reg.submit("priya", "fieldwork", 1200)
    b = reg.submit("tom", "conference", 400)
    _shortlist(reg)(a.app_id, "ok")
    assert reg.get(b.app_id).status == "submitted" and reg.count() == 2
"""
}

_C1_REGRESSION = {
    "test_shortlist_regression.py": _HELPER_COMMON
    + """

def test_submit_withdraw_get_count_unchanged(tmp_path):
    reg, path = _reg(tmp_path)
    a = reg.submit("priya", "fieldwork", 1200)
    assert a.app_id == "A1" and a.status == "submitted" and a.note is None
    assert reg.get("A1") is a and reg.get("A9") is None
    assert reg.withdraw("A1").status == "withdrawn"
    assert reg.get("A1").status == "withdrawn"
    with pytest.raises(KeyError):
        reg.withdraw("A9")
    assert reg.count() == 1
    assert path.read_text().splitlines() == ["submit A1 fieldwork 1200", "withdraw A1"]
"""
}

_C1_CONTRACT = {
    "raise": {
        "test_shortlist_missing.py": _C1_HELPER
        + """

def test_shortlist_unknown_raises_keyerror(tmp_path):
    reg, _ = _reg(tmp_path)
    reg.submit("priya", "fieldwork", 1200)
    with pytest.raises(KeyError):
        _shortlist(reg)("A404", "ok")
"""
    },
    "none": {
        "test_shortlist_missing.py": _C1_HELPER
        + """

def test_shortlist_unknown_returns_none_and_changes_nothing(tmp_path):
    reg, path = _reg(tmp_path)
    a = reg.submit("priya", "fieldwork", 1200)
    before = path.read_text()
    assert _shortlist(reg)("A404", "ok") is None
    assert path.read_text() == before
    assert reg.count() == 1 and reg.get(a.app_id).status == "submitted"
"""
    },
}

_C1_SUPPORT = {
    "test_shortlist_errors.py": _C1_HELPER
    + """

def test_submit_wraps_audit_oserror(tmp_path, monkeypatch):
    reg, _ = _reg(tmp_path)
    monkeypatch.setattr(audit, "append_entry", _boom)
    with pytest.raises(ScholarshipError) as ei:
        reg.submit("priya", "fieldwork", 1200)
    assert isinstance(ei.value.__cause__, OSError)


def test_withdraw_wraps_audit_oserror(tmp_path, monkeypatch):
    reg, _ = _reg(tmp_path)
    a = reg.submit("priya", "fieldwork", 1200)
    monkeypatch.setattr(audit, "append_entry", _boom)
    with pytest.raises(ScholarshipError):
        reg.withdraw(a.app_id)


def test_shortlist_wraps_audit_oserror(tmp_path, monkeypatch):
    reg, _ = _reg(tmp_path)
    a = reg.submit("priya", "fieldwork", 1200)
    monkeypatch.setattr(audit, "append_entry", _boom)
    with pytest.raises(ScholarshipError) as ei:
        _shortlist(reg)(a.app_id, "ok")
    assert isinstance(ei.value.__cause__, OSError)
"""
}

_SHORTLIST_RAISE = """
    def shortlist(self, app_id: str, note: str) -> Application:
        app = self._apps[app_id]
        shortlisted = app.with_changes(status="shortlisted", note=note)
        self._apps[app_id] = shortlisted
        self._audit(f"shortlist {app_id}")
        return shortlisted
"""

_SHORTLIST_NONE = """
    def shortlist(self, app_id: str, note: str) -> Application | None:
        app = self._apps.get(app_id)
        if app is None:
            return None
        shortlisted = app.with_changes(status="shortlisted", note=note)
        self._apps[app_id] = shortlisted
        self._audit(f"shortlist {app_id}")
        return shortlisted
"""


def _gold1(state: str) -> str:
    body = _SHORTLIST_RAISE if state == "raise" else _SHORTLIST_NONE
    return _REGISTRY.replace("\n    def get(", body + "\n    def get(", 1)


_REQ1 = Request(
    text=(
        "Add a public method `shortlist(app_id, note)` on Registry for the committee's "
        'first pass: it sets the application status to "shortlisted", stores the '
        "committee note on the application, writes the audit entry `shortlist <app_id>` "
        "and returns the updated application."
    ),
    target="scholarships/registry.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold={"raise": _gold1("raise"), "none": _gold1("none")},
)

# ----------------------------------------------------------------- checkpoint 2: award

_C2_HELPER = (
    _HELPER_COMMON
    + """

def _award(reg):
    fn = getattr(reg, "award", None) or getattr(reg, "award_application", None)
    assert fn is not None, "no award method found"
    return fn
"""
)

_C2_FUNCTIONAL = {
    "test_award_functional.py": _C2_HELPER
    + """

def test_award_sets_status_and_amount(tmp_path):
    reg, _ = _reg(tmp_path)
    a = reg.submit("priya", "fieldwork", 1200)
    out = _award(reg)(a.app_id, 900)
    assert out.status == "awarded" and out.amount == 900
    assert out.app_id == a.app_id and out.student == "priya"
    assert reg.get(a.app_id).amount == 900


def test_award_writes_audit_entry_with_amount(tmp_path):
    reg, path = _reg(tmp_path)
    a = reg.submit("priya", "fieldwork", 1200)
    _award(reg)(a.app_id, 900)
    lines = path.read_text().splitlines()
    assert lines[-1] == f"award {a.app_id} 900" and len(lines) == 2


def test_award_keeps_note_and_other_applications(tmp_path):
    reg, _ = _reg(tmp_path)
    a = reg.submit("priya", "fieldwork", 1200)
    b = reg.submit("tom", "conference", 400)
    reg.shortlist(a.app_id, "strong references")
    out = _award(reg)(a.app_id, 1200)
    assert out.note == "strong references"
    assert reg.get(b.app_id).status == "submitted" and reg.count() == 2
"""
}

_C2_REGRESSION = {
    "test_award_regression.py": _HELPER_COMMON
    + """

def test_submit_withdraw_shortlist_get_unchanged(tmp_path):
    reg, path = _reg(tmp_path)
    a = reg.submit("priya", "fieldwork", 1200)
    assert reg.get("A1") is a and reg.get("A9") is None
    assert reg.shortlist("A1", "ok").status == "shortlisted"
    assert reg.shortlist("A9", "ok") is None
    assert reg.withdraw("A1").status == "withdrawn"
    assert reg.get("A1").status == "withdrawn"
    with pytest.raises(KeyError):
        reg.withdraw("A9")
    assert reg.count() == 1
    assert path.read_text().splitlines() == ["submit A1 fieldwork 1200", "shortlist A1", "withdraw A1"]
"""
}

_C2_CONTRACT = {
    "raise": {
        "test_award_missing.py": _C2_HELPER
        + """

def test_award_unknown_raises_keyerror(tmp_path):
    reg, _ = _reg(tmp_path)
    reg.submit("priya", "fieldwork", 1200)
    with pytest.raises(KeyError):
        _award(reg)("A404", 900)
"""
    },
    "none": {
        "test_award_missing.py": _C2_HELPER
        + """

def test_award_unknown_returns_none_and_changes_nothing(tmp_path):
    reg, path = _reg(tmp_path)
    a = reg.submit("priya", "fieldwork", 1200)
    before = path.read_text()
    assert _award(reg)("A404", 900) is None
    assert path.read_text() == before
    assert reg.count() == 1 and reg.get(a.app_id).amount == 1200
"""
    },
}

_C2_SUPPORT = {
    "test_award_errors.py": _C2_HELPER
    + """

def test_submit_and_withdraw_wrap_audit_oserror(tmp_path, monkeypatch):
    reg, _ = _reg(tmp_path)
    a = reg.submit("priya", "fieldwork", 1200)
    monkeypatch.setattr(audit, "append_entry", _boom)
    with pytest.raises(ScholarshipError):
        reg.submit("tom", "conference", 400)
    with pytest.raises(ScholarshipError):
        reg.withdraw(a.app_id)


def test_shortlist_wraps_audit_oserror(tmp_path, monkeypatch):
    reg, _ = _reg(tmp_path)
    a = reg.submit("priya", "fieldwork", 1200)
    monkeypatch.setattr(audit, "append_entry", _boom)
    with pytest.raises(ScholarshipError):
        reg.shortlist(a.app_id, "ok")


def test_award_wraps_audit_oserror(tmp_path, monkeypatch):
    reg, _ = _reg(tmp_path)
    a = reg.submit("priya", "fieldwork", 1200)
    monkeypatch.setattr(audit, "append_entry", _boom)
    with pytest.raises(ScholarshipError) as ei:
        _award(reg)(a.app_id, 900)
    assert isinstance(ei.value.__cause__, OSError)
"""
}

_AWARD_RAISE = """
    def award(self, app_id: str, amount: int) -> Application:
        app = self._apps[app_id]
        awarded = app.with_changes(status="awarded", amount=amount)
        self._apps[app_id] = awarded
        self._audit(f"award {app_id} {amount}")
        return awarded
"""

_AWARD_NONE = """
    def award(self, app_id: str, amount: int) -> Application | None:
        app = self._apps.get(app_id)
        if app is None:
            return None
        awarded = app.with_changes(status="awarded", amount=amount)
        self._apps[app_id] = awarded
        self._audit(f"award {app_id} {amount}")
        return awarded
"""


def _gold2(state: str) -> str:
    # Built on the checkpoint-1 gold under the state then in force (none).
    body = _AWARD_RAISE if state == "raise" else _AWARD_NONE
    return _gold1("none").replace("\n    def get(", body + "\n    def get(", 1)


_REQ2 = Request(
    text=(
        "Add a public method `award(app_id, amount)` on Registry for the final committee "
        'decision: it sets the application status to "awarded", replaces the amount with '
        "the awarded amount, writes the audit entry `award <app_id> <amount>` and returns "
        "the updated application. The committee note is left as it is."
    ),
    target="scholarships/registry.py",
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
        "I run the admin side of a small departmental scholarship fund: a few dozen "
        "student applications a year for fieldwork and conference travel, a committee of "
        "four that meets twice a term, and a finance office that wants a written trail "
        "of every decision. Until now this was email and a shared spreadsheet, and last "
        "year we could not reconstruct why one award was 900 rather than 1200. I am "
        "writing a small `scholarships` package: a Registry that mints application ids, "
        "an Application record and an audit trail file the finance office can read "
        "without any tooling. The trail is one line per action:\n\n```\nsubmit A1 "
        "fieldwork 1200\nsubmit A2 conference 400\nwithdraw A2\n```\n\nA colleague has "
        "a tiny Flask form that will call into this for submissions; the committee "
        "itself will use a CLI. Could you draft the README scope section? The committee "
        "chair assumes this is a full grants system with budgets and reports, and I want "
        "the first paragraph to correct that before anyone asks for dashboards. The "
        "fund is about 20,000 a year, so the spreadsheet stays for the totals.",
    ),
    Turn(
        "assistant",
        "A scope block that heads off the dashboard conversation:\n\n```\n## Scope\n"
        "scholarships records what happened to each application: submitted, withdrawn, "
        "and the committee's decisions. It keeps Application records in memory for the "
        "running process and appends one plain-text line per action to an audit trail "
        "the finance office can read as-is. It does not hold budgets, send email or "
        "produce reports; the spreadsheet stays for totals.\n\n## Non-goals\n- budget "
        "tracking\n- student-facing portal\n- reporting or charts\n```\n\nAnd the usage "
        "block, which doubles as the CLI's mental model:\n\n```python\nfrom "
        "scholarships.registry import Registry\n\nreg = Registry("
        '"/shared/finance/scholarships-2026.txt")\napp = reg.submit("priya", '
        '"fieldwork", 1200)\nprint(app.app_id, app.status)\n```\n\nTaking the audit '
        "path in the constructor keeps the academic-year rollover out of the package: "
        "finance starts a new file, the CLI is pointed at it, nothing else changes. "
        "Old years stay readable as plain files with no migration.",
    ),
    Turn(
        "user",
        "On the audit line format: I am writing `<action> <id> [fields]` with spaces. "
        "Finance asked whether amounts should be on every line or only where they "
        "change, and whether the student name belongs in the trail at all given that "
        "the file sits on a shared drive. Here is a realistic day:\n\n```\nsubmit A1 "
        "fieldwork 1200\nsubmit A2 conference 400\nsubmit A3 fieldwork 800\nwithdraw "
        "A2\n```\n\nNames are deliberately absent, ids only, and finance can join to "
        "the spreadsheet when they need a name. Is that a reasonable privacy line, or "
        "am I making their reconciliation harder than it needs to be for a file that is "
        "already inside the department's share? Finance also asked for the program "
        "name on the submit line, which I have, and for the amount on every line, which "
        "I have resisted because it would duplicate the spreadsheet. The trail is meant "
        "to answer the question we could not answer last year: what happened to this "
        "application, in order, with no edits after the fact.",
    ),
    Turn(
        "assistant",
        "It is the right line. The trail's job is to answer 'what happened to A1 and "
        "when', and the id is enough for that; the name lives in one place, the "
        "registry, which means a name correction never has to touch a file that is "
        "supposed to be append-only. Amounts belong on the lines where they are set or "
        "changed, so `submit` carries the requested amount and a future `award` would "
        "carry the awarded amount, while status-only actions like `withdraw` carry "
        "nothing extra. That also keeps the format testable line by line:\n\n```python\n"
        'def test_withdraw_line_is_bare(tmp_path):\n    path = tmp_path / "a.txt"\n    '
        'reg = Registry(str(path))\n    reg.withdraw(reg.submit("priya", "fieldwork", '
        '1200).app_id)\n    assert path.read_text().splitlines()[-1] == "withdraw A1"\n'
        "```\n\nIf finance later wants a timestamp per line, prepend it in `_audit` and "
        "every line gets it at once, "
        "including the lines written by methods that do not exist yet.",
    ),
    Turn(
        "user",
        "Here are the tests I have so far. I want to know whether reading the audit "
        "file back in tests is sensible or whether I should be mocking `audit`:\n\n"
        "```python\nfrom scholarships.registry import Registry\n\n\ndef "
        "test_submit_mints_sequential_ids(tmp_path):\n    reg = Registry(str(tmp_path / "
        '"a.txt"))\n    assert reg.submit("priya", "fieldwork", 1200).app_id == "A1"\n'
        '    assert reg.submit("tom", "conference", 400).app_id == "A2"\n\n\ndef '
        'test_submit_writes_one_line(tmp_path):\n    path = tmp_path / "a.txt"\n    '
        'reg = Registry(str(path))\n    reg.submit("priya", "fieldwork", 1200)\n    '
        'assert path.read_text().splitlines() == ["submit A1 fieldwork 1200"]\n\n\ndef '
        "test_get_unknown_is_none(tmp_path):\n    assert Registry(str(tmp_path / "
        '"a.txt")).get("A7") is None\n```\n\nThe Flask colleague says everything '
        "should be mocked, but his tests also never catch anything.",
    ),
    Turn(
        "assistant",
        "Read the real file. `audit.append_entry` is three lines and the thing you care "
        "about is the bytes finance will see; mocking it would test the mock. Keep "
        "`tmp_path` so every test has a fresh trail. I would add one end-to-end test "
        "for withdraw, because that is the path the committee will exercise most:\n\n"
        "```python\ndef test_withdraw_updates_record_and_trail(tmp_path):\n    path = "
        'tmp_path / "a.txt"\n    reg = Registry(str(path))\n    a = reg.submit("priya", '
        '"fieldwork", 1200)\n    assert reg.withdraw(a.app_id).status == "withdrawn"\n'
        '    assert path.read_text().splitlines()[-1] == "withdraw A1"\n```\n\nThe one '
        "place a mock earns its keep is the failure path, where you need the audit write "
        "to fail on demand; `monkeypatch.setattr(audit, 'append_entry', boom)` does "
        "that without touching the filesystem. The Flask tests never catch anything "
        "because they mock the registry too, so they assert what the mock was told.",
    ),
    Turn(
        "user",
        "Which brings me to Tuesday. The shared drive dropped for ten minutes and the "
        "Flask form showed the committee chair this, verbatim, in the browser:\n\n```\n"
        'Traceback (most recent call last):\n  File "/srv/grants/app.py", line 58, in '
        'submit_view\n    app = reg.submit(student, program, amount)\n  File "/srv/'
        'grants/scholarships/registry.py", line 17, in submit\n    audit.append_entry('
        'self._audit_path, f"submit {app.app_id} {program} {amount}")\n  File "/srv/'
        'grants/scholarships/audit.py", line 6, in append_entry\n    with open(path, '
        '"a", encoding="utf-8") as fh:\nOSError: [Errno 30] Read-only file system: '
        "'/shared/finance/scholarships-2026.txt'\n```\n\nHe now thinks the system is "
        "broken. I want callers to see one package exception with a readable message "
        "and to be able to catch exactly that, but I do not want try/except in every "
        "method. What is the cleanest structure?",
    ),
    Turn(
        "assistant",
        "One exception class in the package and one private method that every audit "
        "write goes through:\n\n```python\nclass ScholarshipError(Exception):\n    "
        '"""Raised when the audit trail cannot be written."""\n```\n\n```python\ndef '
        "_audit(self, text: str) -> None:\n    try:\n        audit.append_entry(self."
        "_audit_path, text)\n    except OSError as exc:\n        raise ScholarshipError("
        'f"audit write failed: {exc}") from exc\n```\n\n`submit` and `withdraw` call '
        "`_audit` instead of `audit.append_entry`, so the translation lives in exactly "
        "one place, and `from exc` preserves the errno for whoever debugs the share. "
        "The Flask view then catches ScholarshipError and renders 'the audit trail is "
        "unavailable, try again in a few minutes', which is what the chair should have "
        "seen. Note the record is stored before the write, so a retry of the same "
        "submission will mint a second id; that is acceptable for a form but the CLI "
        "should say so. If that bothers you later, move the store into a second step "
        "after the write succeeds; the audit line would then be the source of truth.",
    ),
    Turn(
        "user",
        "That is the convention, and I want it stated: every public Registry method that "
        "writes the audit trail wraps any OSError from `audit.append_entry` in "
        "ScholarshipError, raised `from` the original, and callers never see a raw "
        "OSError. New methods go through `_audit` so this holds automatically.",
    ),
    Turn(
        "assistant",
        "Noted: public Registry methods that touch the audit trail surface I/O failures "
        "only as ScholarshipError chained from the OSError, never raw. Every new audit "
        "write goes through `_audit`.",
    ),
    Turn(
        "user",
        "Second convention, for unknown ids. Methods that act on an application by id, "
        "like `withdraw`, raise KeyError when the id is not in the registry. A bad id "
        "from the CLI is a typo and I want it to fail immediately rather than quietly "
        "do nothing. New methods that act on an id do the same.",
    ),
    Turn(
        "assistant",
        "Understood: id-keyed actions raise KeyError on an unknown application id, "
        "matching `withdraw`. New methods will index `self._apps[app_id]` directly so "
        "nothing is stored or audited for an id that does not exist.",
    ),
    Turn(
        "user",
        "I have to change that. The committee's import script pulls ids out of the "
        "spreadsheet and about one in twenty is stale, so the CLI crashes halfway through "
        "every meeting. From now on, new methods that act on an id return None when the "
        "id is unknown and change nothing: no audit line, no exception. `withdraw` stays "
        "as it is; I am not touching existing behaviour during term. The import script "
        "logs the ids it skipped at the end, so nothing is silently lost on our side, "
        "and the committee can fix the spreadsheet at their leisure.",
    ),
    Turn(
        "assistant",
        "Understood: the rule for new id-keyed methods is now return None on an unknown "
        "id with no state change and no audit line; `withdraw` keeps raising KeyError. "
        "New methods will look up with `self._apps.get(app_id)` and return None before "
        "any write. The return type on those methods becomes `Application | None`, "
        "and the CLI can print 'no such application' when it sees None.",
    ),
    Turn(
        "user",
        "Right, let's get the committee's first pass working before the meeting. I will "
        "paste the current files with each request so you see the real state of the code "
        "rather than my memory of it.",
    ),
    Turn(
        "assistant",
        "Ready when you are. Send the request and I will return the full registry module.",
    ),
]

_EVENT = (
    "Reverting the unknown-id change from earlier: the import script now validates ids "
    "against the registry before calling anything, so new Registry methods that act on "
    "an application id go back to raising KeyError when the id is unknown. `shortlist` "
    "stays as written (returning None) and `withdraw` was never changed; only new "
    "methods follow the reinstated rule."
)


def build() -> Session:
    return Session(
        id="S40",
        project="scholarships",
        target_family="missing_record",
        support_family="error_surface",
        lifecycle="reinstatement",
        files=_FILES,
        prefix=_PREFIX,
        states=("raise", "none"),
        state_at=("none", "raise"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10, 12),
        tags={"support_state": "wrap"},
    )
