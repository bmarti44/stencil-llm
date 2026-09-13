# ruff: noqa: E501
"""S15: bike repairs — naming (target, scope) x logging (support, silent)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '"""spokeshop package."""\n'

_MODEL = '''"""Repair job records."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Job:
    job_id: str
    bike: str
    description: str
    status: str = "queued"
    mechanic: str | None = None
'''

_WORKSHOP_HEAD = '''"""In-memory repair queue."""
{extra_imports}
from spokeshop.model import Job


class Workshop:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {{}}
        self._next = 1

    def open_job(self, bike: str, description: str) -> Job:
        job = Job(job_id=f"J{{self._next}}", bike=bike, description=description)
        self._next += 1
        self._jobs[job.job_id] = job
        return job

    def find(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    def count(self) -> int:
        return len(self._jobs)
'''

_WORKSHOP = _WORKSHOP_HEAD.format(extra_imports="")

_FILES = {
    "spokeshop/__init__.py": _INIT,
    "spokeshop/model.py": _MODEL,
    "spokeshop/workshop.py": _WORKSHOP,
}

# ----------------------------------------------------------------- checkpoint 1: start

_C1_HELPER = """import logging

from spokeshop.workshop import Workshop


def _start(shop):
    fn = getattr(shop, "start_job", None) or getattr(shop, "job_start", None)
    assert fn is not None, "no start method found"
    return fn
"""

_C1_FUNCTIONAL = {
    "test_start_functional.py": _C1_HELPER
    + """

def test_start_sets_status_and_mechanic():
    w = Workshop()
    j = w.open_job("red Brompton", "brake cable frayed")
    out = _start(w)(j.job_id, "priya")
    assert out.status == "in_progress" and out.mechanic == "priya"
    stored = w.find(j.job_id)
    assert stored.status == "in_progress" and stored.mechanic == "priya"


def test_start_keeps_bike_and_description():
    w = Workshop()
    j = w.open_job("blue Surly", "true rear wheel")
    out = _start(w)(j.job_id, "tom")
    assert out.job_id == j.job_id
    assert out.bike == "blue Surly" and out.description == "true rear wheel"


def test_start_already_started_is_noop():
    w = Workshop()
    j = w.open_job("red Brompton", "brake cable frayed")
    first = _start(w)(j.job_id, "priya")
    out = _start(w)(j.job_id, "tom")
    assert out == first and out.mechanic == "priya"
    assert w.find(j.job_id) == first


def test_start_unknown_raises_keyerror():
    w = Workshop()
    try:
        _start(w)("J77", "priya")
    except KeyError:
        return
    raise AssertionError("expected KeyError for an unknown job")


def test_start_keeps_the_other_job_and_the_count():
    w = Workshop()
    other = w.open_job("blue Surly", "true rear wheel")
    kept = _start(w)(other.job_id, "tom")
    target = w.open_job("red Brompton", "brake cable frayed")
    out = _start(w)(target.job_id, "priya")
    assert out.status == "in_progress" and out.mechanic == "priya"
    assert w.count() == 2
    back = w.find(other.job_id)
    assert back is not None, "starting one job dropped the other"
    assert back == kept and back.status == "in_progress"
    assert back.mechanic == "tom" and back.bike == "blue Surly"
    assert back.description == "true rear wheel"


def test_start_noop_keeps_the_other_job_and_every_field():
    w = Workshop()
    other = w.open_job("blue Surly", "true rear wheel")
    target = w.open_job("red Brompton", "brake cable frayed")
    first = _start(w)(target.job_id, "priya")
    out = _start(w)(target.job_id, "tom")
    assert out == first and out.mechanic == "priya"
    stored = w.find(target.job_id)
    assert stored == first and stored.status == "in_progress"
    assert stored.bike == "red Brompton"
    assert w.count() == 2
    back = w.find(other.job_id)
    assert back is not None and back == other
    assert back.status == "queued" and back.mechanic is None
"""
}

_C1_REGRESSION = {
    "test_start_regression.py": """from spokeshop.workshop import Workshop


def test_open_find_count_unchanged():
    w = Workshop()
    j = w.open_job("red Brompton", "brake cable frayed")
    assert j.job_id == "J1" and j.status == "queued" and j.mechanic is None
    assert w.find("J1") is j
    assert w.find("J2") is None
    assert w.count() == 1


def test_open_keeps_every_earlier_job():
    w = Workshop()
    first = w.open_job("blue Surly", "true rear wheel")
    second = w.open_job("red Brompton", "brake cable frayed")
    assert w.count() == 2
    assert w.find(first.job_id) == first
    assert w.find(second.job_id) == second
"""
}

_C1_CONTRACT = {
    "verb_noun": {
        "test_start_naming.py": """from spokeshop.workshop import Workshop


def test_start_is_verb_noun():
    assert hasattr(Workshop, "start_job")
    assert not hasattr(Workshop, "job_start")
"""
    },
    "noun_verb": {
        "test_start_naming.py": """from spokeshop.workshop import Workshop


def test_start_is_noun_verb():
    assert hasattr(Workshop, "job_start")
    assert not hasattr(Workshop, "start_job")
"""
    },
}

_C1_SUPPORT = {
    "test_start_logging.py": _C1_HELPER
    + """

def test_starting_started_job_logs_nothing(caplog):
    w = Workshop()
    j = w.open_job("red Brompton", "brake cable frayed")
    _start(w)(j.job_id, "priya")
    with caplog.at_level(logging.DEBUG):
        _start(w)(j.job_id, "tom")
    assert caplog.records == [], [r.getMessage() for r in caplog.records]
"""
}


def _gold1(name: str) -> str:
    return (
        _WORKSHOP_HEAD.format(
            extra_imports="\nfrom dataclasses import replace\n"
        ).rstrip("\n")
        + f"""

    def {name}(self, job_id: str, mechanic: str) -> Job:
        job = self._jobs[job_id]
        if job.status == "in_progress":
            return job
        started = replace(job, status="in_progress", mechanic=mechanic)
        self._jobs[job_id] = started
        return started
"""
    )


_REQ1 = Request(
    text=(
        "Add a public method on Workshop that starts a job: it takes the job id and the "
        'mechanic\'s name, stores the job with status "in_progress" and that mechanic, '
        "and returns it. An unknown id raises KeyError. Starting a job that is already "
        "in progress is the notable no-op case: the job is returned unchanged, keeping "
        "the mechanic who already has it."
    ),
    target="spokeshop/workshop.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold={"verb_noun": _gold1("start_job"), "noun_verb": _gold1("job_start")},
)

# ----------------------------------------------------------------- checkpoint 2: jobs for bike

_C2_HELPER = """import logging

from spokeshop.workshop import Workshop


def _for_bike(shop):
    fn = getattr(shop, "jobs_list", None) or getattr(shop, "list_jobs", None)
    assert fn is not None, "no listing method found"
    return fn
"""

_C2_FUNCTIONAL = {
    "test_list_functional.py": _C2_HELPER
    + """

def test_list_returns_jobs_for_that_bike_in_order():
    w = Workshop()
    a = w.open_job("red Brompton", "brake cable frayed")
    w.open_job("blue Surly", "true rear wheel")
    b = w.open_job("red Brompton", "replace chain")
    assert _for_bike(w)("red Brompton") == [a, b]


def test_list_reflects_current_records():
    w = Workshop()
    j = w.open_job("blue Surly", "true rear wheel")
    start = getattr(w, "start_job", None) or getattr(w, "job_start", None)
    started = start(j.job_id, "priya")
    assert _for_bike(w)("blue Surly") == [started]


def test_list_unknown_bike_is_empty_list():
    w = Workshop()
    w.open_job("red Brompton", "brake cable frayed")
    out = _for_bike(w)("green Bianchi")
    assert out == [] and isinstance(out, list)
    assert w.count() == 1


def _start(shop):
    fn = getattr(shop, "start_job", None) or getattr(shop, "job_start", None)
    assert fn is not None, "no start method found"
    return fn


def test_list_after_starting_one_job_still_sees_the_others():
    w = Workshop()
    a = w.open_job("red Brompton", "brake cable frayed")
    b = w.open_job("blue Surly", "true rear wheel")
    started = _start(w)(b.job_id, "priya")
    assert started.status == "in_progress" and started.mechanic == "priya"
    assert _for_bike(w)("blue Surly") == [started]
    assert _for_bike(w)("red Brompton") == [a]
    assert w.count() == 2
    back = w.find(a.job_id)
    assert back is not None, "starting one job dropped the other"
    assert back == a and back.status == "queued" and back.mechanic is None


def test_list_changes_nothing_in_the_store():
    w = Workshop()
    a = w.open_job("red Brompton", "brake cable frayed")
    b = w.open_job("blue Surly", "true rear wheel")
    kept = _start(w)(b.job_id, "tom")
    assert _for_bike(w)("red Brompton") == [a]
    assert _for_bike(w)("blue Surly") == [kept]
    assert w.count() == 2
    assert w.find(a.job_id) == a
    back = w.find(b.job_id)
    assert back is not None and back == kept
    assert back.status == "in_progress" and back.mechanic == "tom"
    assert back.bike == "blue Surly"
"""
}

_C2_REGRESSION = {
    "test_list_regression.py": """from spokeshop.workshop import Workshop


def _start(shop):
    return getattr(shop, "start_job", None) or getattr(shop, "job_start", None)


def test_open_find_count_start_unchanged():
    w = Workshop()
    j = w.open_job("red Brompton", "brake cable frayed")
    assert w.find("J1") is j and w.count() == 1
    out = _start(w)(j.job_id, "priya")
    assert out.status == "in_progress" and out.mechanic == "priya"
    assert _start(w)(j.job_id, "tom") == out


def test_start_keeps_the_other_job():
    w = Workshop()
    other = w.open_job("blue Surly", "true rear wheel")
    kept = _start(w)(other.job_id, "tom")
    target = w.open_job("red Brompton", "brake cable frayed")
    out = _start(w)(target.job_id, "priya")
    assert out.status == "in_progress" and out.mechanic == "priya"
    assert w.count() == 2
    back = w.find(other.job_id)
    assert back is not None, "starting one job dropped the other"
    assert back == kept and back.status == "in_progress"
    assert back.mechanic == "tom" and back.bike == "blue Surly"
"""
}

_C2_CONTRACT = {
    "verb_noun": {
        "test_list_naming.py": """from spokeshop.workshop import Workshop


def test_list_is_verb_noun():
    assert hasattr(Workshop, "list_jobs")
    assert not hasattr(Workshop, "jobs_list")
"""
    },
    "noun_verb": {
        "test_list_naming.py": """from spokeshop.workshop import Workshop


def test_list_is_noun_verb():
    assert hasattr(Workshop, "jobs_list")
    assert not hasattr(Workshop, "list_jobs")
"""
    },
}

_C2_SUPPORT = {
    "test_list_logging.py": _C2_HELPER
    + """

def test_listing_unknown_bike_logs_nothing(caplog):
    w = Workshop()
    w.open_job("red Brompton", "brake cable frayed")
    with caplog.at_level(logging.DEBUG):
        _for_bike(w)("green Bianchi")
    assert caplog.records == [], [r.getMessage() for r in caplog.records]
"""
}


def _gold2(name: str) -> str:
    # Built on the checkpoint-1 gold under the state then in force (verb_noun).
    return (
        _gold1("start_job").rstrip("\n")
        + f"""

    def {name}(self, bike: str) -> list[Job]:
        return [job for job in self._jobs.values() if job.bike == bike]
"""
    )


_REQ2 = Request(
    text=(
        "Add a public method on Workshop that lists the jobs for one bike: it takes the "
        "bike name and returns the Job records for that bike as a list in creation "
        "order, reflecting their current status. It changes nothing. A bike that has no "
        "jobs at all is the notable case: return an empty list."
    ),
    target="spokeshop/workshop.py",
    functional_tests=_C2_FUNCTIONAL,
    regression_tests=_C2_REGRESSION,
    contract_tests=_C2_CONTRACT,
    support_tests=_C2_SUPPORT,
    gold={"verb_noun": _gold2("list_jobs"), "noun_verb": _gold2("jobs_list")},
)

# ----------------------------------------------------------------- prefix (16 turns)

_PREFIX = [
    Turn(
        "user",
        "I volunteer at a community bike workshop on Saturdays and we track repair jobs "
        "on a whiteboard, which works until someone wipes it. I want to write spokeshop, "
        "a small Python package that keeps the repair queue in memory and that a couple "
        "of scripts can drive: open a job when a bike comes in, start it when a mechanic "
        "picks it up, print the board. It runs on the shop laptop; the board script "
        "writes out a text file that we print and pin up. Nothing shared, nothing "
        "networked. This is the README I have so far:\n\n```\n# spokeshop\n\nA repair "
        "queue for a volunteer bike workshop. Jobs are identified as J1, J2, ... in the "
        'order they arrive and each job belongs to one bike, described free-form ("red '
        'Brompton", "blue Surly"). A job is queued until a mechanic starts it.\n\n## '
        "Scripts\n- `board.py` prints the queue grouped by status\n- `intake.py` opens "
        "jobs from a CSV the front desk fills in\n```\n\nDoes that need anything else "
        "before I show it to the other volunteers?",
    ),
    Turn(
        "assistant",
        "It reads well. I would add two lines that head off the questions volunteers "
        "will ask on the first Saturday: what happens when the laptop is closed (state "
        "is lost unless a script saved it), and that the package itself does no I/O. "
        "Something like:\n\n```\n## Persistence\nThe library keeps jobs in memory only. "
        "`board.py` and `intake.py` load and save `queue.json` in the shop folder at the "
        "start and end of each run; nothing is written automatically.\n\n## Non-goals\n"
        "- customer contact details\n- parts inventory\n- anything multi-user\n```\n\n"
        "Keeping I/O out of the `Workshop` class is what makes it pleasant to test: a "
        "test constructs `Workshop()`, opens two jobs and asserts on the records that "
        "come back, no temp files needed. The CSV intake can stay a ten-line script "
        "that loops over rows and calls `open_job`:\n\n```python\nimport csv\n\nfrom "
        'spokeshop.workshop import Workshop\n\nshop = Workshop()\nwith open("intake.csv", '
        'newline="") as fh:\n    for row in csv.DictReader(fh):\n        '
        'shop.open_job(row["bike"], row["description"])\nprint(shop.count(), '
        '"jobs queued")\n```',
    ),
    Turn(
        "user",
        "Here is the model I have. A frozen dataclass Job with job_id, bike, "
        'description, status ("queued" to start, then "in_progress", then "done") '
        "and an optional mechanic. I went frozen after reading that mutable records make "
        "the board script lie when it holds a stale copy. Question: should the status "
        "transitions be enforced somewhere, like a small table of allowed moves, or is "
        "that over-engineering for three states? The transitions I care about are "
        "queued -> in_progress when a mechanic starts a job, and in_progress -> done "
        "when they finish. Nothing goes backwards, and I do not expect that to change. "
        "The intake CSV has just three columns:\n\n```\nbike,description,contact\n"
        "red Brompton,brake cable frayed,555-0142\nblue Surly,true rear wheel,555-0199\n"
        "```\n\nand contact never enters the package, it stays in the CSV. The front "
        "desk volunteers also asked whether a bike can have two open jobs at once, for "
        "example brakes and a wheel true brought in together. I said yes: two rows, two "
        "jobs, same bike string, because the mechanics pick them up separately.",
    ),
    Turn(
        "assistant",
        "For three states in a fixed line, a transition table is more machinery than "
        "value. Put the rule inside each action method instead: the method that starts a "
        "job checks the status it expects and either does the transition or leaves the "
        "record alone, and the method that finishes a job does likewise. Each method "
        "then documents its own precondition, which is easier to read than a table "
        "somewhere else. The change pattern is the same for every action:\n\n```python\n"
        'job = self._jobs[job_id]\nupdated = replace(job, status="in_progress", '
        "mechanic=mechanic)\nself._jobs[job_id] = updated\nreturn updated\n```\n\nwith "
        "`dataclasses.replace` keeping the record frozen. If a fourth state ever "
        "appears, that is the moment to revisit a table; until then, the per-method "
        "check is the honest amount of code. The finishing method would mirror it, "
        "checking for `in_progress` before moving to `done`, and a test for the "
        "precondition is a three-liner: open a job, finish it without starting it, "
        "assert the record still says queued.",
    ),
    Turn(
        "user",
        "Makes sense. Here are the tests I have for the current Workshop class, all "
        "passing:\n\n```python\nfrom spokeshop.workshop import Workshop\n\n\ndef "
        "test_open_assigns_sequential_ids():\n    w = Workshop()\n    assert w.open_job("
        '"red Brompton", "brakes").job_id == "J1"\n    assert w.open_job("blue Surly", '
        '"wheel").job_id == "J2"\n\n\ndef test_new_job_is_queued_without_mechanic():\n'
        '    j = Workshop().open_job("red Brompton", "brakes")\n    assert j.status == '
        '"queued"\n    assert j.mechanic is None\n\n\ndef '
        'test_find_missing_returns_none():\n    assert Workshop().find("J9") is None\n'
        "```\n\nI am unsure about `find` returning None. In `board.py` I call it while "
        "rendering and a None slipped through last week and printed 'None' on the board, "
        "and the next line in that script then blew up:\n\n```\nTraceback (most recent "
        'call last):\n  File "board.py", line 31, in <module>\n    print(job.status)\n'
        "AttributeError: 'NoneType' object has no attribute 'status'\n```",
    ),
    Turn(
        "assistant",
        "Keep `find` returning None; the name says it may miss and the board script "
        "should branch on it. The bug you hit is the classic None-propagation trap, and "
        "the fix belongs in the script, not the lookup. Actions are the other case: "
        "starting or finishing a job that does not exist is a caller mistake, so those "
        "methods raise KeyError by indexing the dict directly. Two rules, easy to "
        "remember: lookups return None, actions raise KeyError. For the board, guard the "
        'render:\n\n```python\njob = shop.find(job_id)\nif job is None:\n    print(f"?? '
        '{job_id} not in queue")\n    continue\nprint(f"{job.job_id} [{job.status}] '
        '{job.bike}: {job.description}")\n```\n\nThat prints a visible marker instead of '
        "the word None, and the traceback you would otherwise get points at the script. "
        "For the board layout itself, a fixed-width line per job reads best when pinned "
        "up:\n\n```\nQUEUED\n  J3  blue Surly        true rear wheel\nIN_PROGRESS\n  J1  "
        "red Brompton      brake cable frayed   (priya)\n```",
    ),
    Turn(
        "user",
        "One thing I want to settle before adding more methods: should the package say "
        "anything when something odd happens? On the last project I worked on, the "
        "library printed to stdout and it wrecked the output of every script that used "
        "it. Then we switched it to logging and the volunteers got a wall of WARNING "
        "lines on the terminal because nobody configured a handler and Python's "
        "last-resort handler printed everything. Here is the kind of thing I mean, from "
        "that project:\n\n```\nWARNING:queue.store:job 14 already started\nWARNING:"
        "queue.store:job 14 already started\nWARNING:queue.store:job 15 already started\n"
        "J14 in_progress\nJ15 in_progress\n```\n\nThe output of the board got buried, "
        "and the fix at the time was a `logging.disable()` call at the top of every "
        "script, which is its own kind of mess because then real problems went quiet "
        "too. I would rather decide once for spokeshop and write it in the README so "
        "the next volunteer does not relitigate it. What is the sane default for a "
        "library this small?",
    ),
    Turn(
        "assistant",
        "The sane default for a small library is silence. A library should not decide "
        "what the user sees; it returns values and raises exceptions for actual "
        "errors, and the script that owns the terminal decides what to print. The "
        "wall of WARNING lines you saw is what happens when a library logs and no one "
        "configures logging: Python's last-resort handler writes warnings and above to "
        "stderr. Returning the record unchanged for a harmless no-op already tells the "
        "caller everything, since it can compare before and after if it cares. If the "
        "board script wants to flag oddities, it can do so itself:\n\n```python\nbefore "
        "= shop.find(job_id)\nafter = shop.start_job(job_id, mechanic)\nif after == "
        'before:\n    print(f"note: {job_id} was already started")\n```\n\nThat keeps '
        "the decision about noise in the one place that knows the audience, and it "
        "means no script ever needs `logging.disable()` to get a clean terminal. Write "
        "the one-line rule in the README under a 'Logging' heading and it is settled.",
    ),
    Turn(
        "user",
        "Agreed, so let's make it a rule: the spokeshop package never logs. No "
        "logging.warning for odd-but-harmless conditions like a no-op, no info, no "
        "debug, no print. A method that hits such a condition just returns the record "
        "and the caller decides what to say.",
    ),
    Turn(
        "assistant",
        "Noted: no log records of any level from the package, and no printing. Notable "
        "but harmless conditions are handled by returning the record as it stands; "
        "actual errors raise exceptions. I will not create a module logger at all so "
        "there is nothing to accidentally call.",
    ),
    Turn(
        "user",
        "Naming: public Workshop methods are verb_noun, like open_job. Anything new "
        "follows that pattern so the class reads like a list of things you can do to the "
        "queue.",
    ),
    Turn(
        "assistant",
        "Understood: verb_noun for public Workshop methods, matching open_job. A method "
        "that starts a job is start_job, one that finishes it is finish_job, and so on. "
        "Private helpers can be named freely.",
    ),
    Turn(
        "user",
        "For later, not now: `board.py` will want the queue grouped by status. I "
        'imagine something like:\n\n```python\nfor status in ("queued", '
        '"in_progress", "done"):\n    print(status.upper())\n    for job in '
        'shop.jobs_by_status(status):\n        print(f"  {job.job_id} {job.bike}: '
        '{job.description}")\n```\n\nwhere jobs_by_status does not exist yet and the '
        "name is a placeholder.",
    ),
    Turn(
        "assistant",
        "That will be a one-line comprehension over `self._jobs.values()` filtered on "
        "status, in insertion order, which is arrival order because ids are sequential. "
        "Nothing about the current class needs to change to support it, and the board "
        "script can keep the fixed-width formatting we sketched earlier.",
    ),
    Turn(
        "user",
        "Good. Let's do the first real method now; Saturday is coming and I want "
        "mechanics to be able to claim jobs from the intake list. I will paste the "
        "current files with every request so you always see the real state.",
    ),
    Turn(
        "assistant",
        "Ready. Send the request with the files and I will return the complete workshop "
        "module.",
    ),
]

_EVENT = (
    "Scoped exception to the naming convention, effective now: read-only query methods "
    "on Workshop, meaning public methods that return data without changing any job, are "
    "named noun_verb (jobs_list style) so that all the queries sort together in the "
    "class. Mutating actions keep verb_noun, and existing names stay as they are."
)


def build() -> Session:
    return Session(
        id="S15",
        project="spokeshop",
        target_family="naming",
        support_family="logging",
        lifecycle="scope",
        files=_FILES,
        prefix=_PREFIX,
        states=("verb_noun", "noun_verb"),
        state_at=("verb_noun", "noun_verb"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10),
    )
