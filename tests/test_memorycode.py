"""CPU checks for the MemoryCode-derived contract (results/memorycode-derived/).

Rendering, label isolation, packing, checker fixtures per family, auto determinism."""

import copy
import json
from pathlib import Path

import pytest

from stencil import memorycode as mc

ROOT = Path(__file__).resolve().parent.parent
TOKENIZER = ROOT / "models/qwen3-1.7b-hf/tokenizer.json"
needs_dataset = pytest.mark.skipif(not mc.DATASET.exists(), reason="vendor/memorycode")


class WordTokenizer:
    class _Enc:
        def __init__(self, ids):
            self.ids = ids

    def encode(self, text):
        return self._Enc(text.split())


class FakeClassifier:
    """Admits every sentence containing 'always'; proposes supersedes when the new
    sentence shares its first two words with the old rule and differs."""

    thresholds = {
        "cancels": 0.5,
        "completes": 0.5,
        "reinstates": 0.5,
        "supersedes": 0.9,
    }
    admission_bound = "positive_proposal"

    def relations(self, pairs):
        out = []
        for pair in pairs:
            new = pair["target_span"]["text"]
            old = pair["old_rule"]["text"]
            same_topic = "variable names" in new and "variable names" in old
            supersedes = same_topic and new != old
            p = [0.0, 1.0, 0.0, 0.0, 0.0] if supersedes else [1.0, 0.0, 0.0, 0.0, 0.0]
            out.append(dict(probabilities=p, overflow=False))
        return out

    def admission(self, spans, previous):
        return [
            dict(
                probabilities=[0.0, 1.0, 0.0] if "always" in s else [1.0, 0.0, 0.0],
                overflow=False,
            )
            for s in spans
        ]


def _dialogue():
    return {
        "context": {"mentor": "Maria", "mentee": "David"},
        "sessions": [
            {
                "type": ["instruction-add"],
                "text": "Maria: Hi David. From now on always end variable names "
                "with _m. Also always use annotations for methods."
                "\n\nDavid: Sure thing.",
                "session_regex": [],
                "history_regex": [],
                "session_eval_query": [],
                "history_eval_query": [],
            },
            {
                "type": ["instruction-update"],
                "text": "Maria: Update: from now on always end variable names with _n."
                "\n\nDavid: Got it.",
                "session_regex": [],
                "history_regex": [],
                "session_eval_query": [],
                "history_eval_query": [],
            },
            {
                "type": ["filler-add"],
                "text": "Maria: Please write the code.\n\nDavid: Ok.",
                "session_regex": [],
                "history_regex": [["variable", ".*_n$"], ["method annotation", True]],
                "session_eval_query": [],
                "history_eval_query": ["binary tree class"],
            },
        ],
        # per-session EVENTS (vendored generator semantics): session 0 introduces
        # 12/5 and 17/0, session 1 updates 12 -> 6, session 2 is filler ([-1]).
        "instructions": [[[12, 5], [17, 0]], [[12, 6]], [-1]],
    }


def test_history_and_reminder_prompts():
    d = _dialogue()
    hist = mc.user_message(d, 2, "binary tree class", "history", "")
    assert " Session 0 " in hist and " Session 2 " in hist and mc.HEADER not in hist
    rem = mc.render_reminder(["always end variable names with _n."])
    auto = mc.user_message(d, 2, "binary tree class", "auto", rem)
    assert " Session 0 " not in auto and " Session 2 " in auto
    assert auto.index(mc.HEADER) < auto.index("Based on information provided")
    assert auto.endswith("including any possible updates.")
    prompt = mc.chat_prompt(auto)
    assert prompt.startswith("<|im_start|>user\n") and prompt.endswith(mc.OPENER)


def test_candidates_and_label_isolation():
    d = _dialogue()
    stripped = copy.deepcopy(d)
    del stripped["instructions"]
    for s in stripped["sessions"]:
        for k in ("type", "session_regex", "history_regex", "history_eval_query"):
            del s[k]
    cands = mc.mentor_sentences(d, 2)
    assert [c["text"] for c in cands] == [
        "Hi David.",
        "From now on always end variable names with _m.",
        "Also always use annotations for methods.",
        "Update: from now on always end variable names with _n.",
    ]
    assert cands == mc.mentor_sentences(stripped, 2)
    from stencil.focus3 import Runtime

    a = mc.auto_live(d, 2, Runtime(FakeClassifier()))
    b = mc.auto_live(stripped, 2, Runtime(FakeClassifier()))
    assert a == b
    with pytest.raises(KeyError):
        mc.oracle_sentences(stripped, 2, {"instructions": []})


def test_auto_adapter_admits_and_supersedes():
    from stencil.focus3 import Runtime

    d = _dialogue()
    out = mc.auto_live(d, 2, Runtime(FakeClassifier()))
    assert out["admitted"] >= 2 and out["relations_applied"] >= 1
    assert out["sentences"] == [
        "Also always use annotations for methods.",
        "Update: from now on always end variable names with _n.",
    ]
    assert out == mc.auto_live(d, 2, Runtime(FakeClassifier()))  # deterministic


def test_oracle_sentences_ordered_by_introduction():
    topics = {
        "instructions": [
            {"id": 12, "text": ["a", "b", "c", "d", "e", "with _m", "with _n"]},
            {"id": 17, "text": ["annotations"]},
        ]
    }
    d = _dialogue()
    # filler session after an update: the live set is the REPLAY (latest update per
    # pivot, ordered by first introduction), not the current session's events
    assert mc.live_instructions(d, 2) == [(12, 6), (17, 0)]
    assert mc.live_instructions(d, 0) == [(12, 5), (17, 0)]
    assert mc.instruction_events(d, 2) == []
    assert mc.oracle_sentences(d, 2, topics) == ["with _n", "annotations"]
    assert mc.oracle_sentences(d, 1, topics) == ["with _n", "annotations"]
    assert mc.oracle_sentences(d, 0, topics) == ["with _m", "annotations"]


@needs_dataset
def test_live_set_reproduces_history_regex_on_every_item():
    """The replayed live set implies exactly the dataset's history_regex checks
    (instrument repair 2026-09-12; 224 items over both cohorts)."""
    topics = mc.load_topics()
    for path in (
        ROOT / "results/memorycode-long/items.json",
        ROOT / "results/memorycode-derived/items.json",
    ):
        for it in json.loads(path.read_text())["items"]:
            d = mc.load_dialogue(it["dialogue"])
            got = sorted(
                json.dumps(r) for r in mc.live_regexes(d, it["session"], topics)
            )
            exp = sorted(
                json.dumps(r) for r in d["sessions"][it["session"]]["history_regex"]
            )
            assert got == exp, it["id"]


def test_speaker_split_handles_non_ascii_names():
    assert mc.split_speaker("Jean-Aimé: Use tabs.", "Jean-Aimé", "Lucas") == (
        "mentor",
        "Use tabs.",
    )
    assert mc.split_speaker("Lucas: Ok.", "Jean-Aimé", "Lucas") == ("mentee", "Ok.")
    assert mc.split_speaker("Narrator: x", "Jean-Aimé", "Lucas") == (
        "other",
        "Narrator: x",
    )
    d = {
        "context": {"mentor": "Jean-Aimé", "mentee": "Lucas"},
        "sessions": [{"text": "Jean-Aimé: Always use tabs. Thanks.\nLucas: Sure."}],
    }
    assert mc.speaker_lines(d, 0) == [
        ("mentor", "Always use tabs. Thanks."),
        ("mentee", "Sure."),
    ]
    assert [m[:2] for m in mc.focus_session_messages(d, 0)] == [
        ("separator", ""),
        ("user", "Always use tabs. Thanks."),
        ("other", ""),
    ]


def test_pack_newest_first_stops_at_first_overflow():
    tok = WordTokenizer()
    ordered = ["one two three", "four", "five six seven eight", "nine"]
    # header = 5 words; a bullet = "-" + its words: nine 2, five.. 5, four 2, one.. 4
    assert mc.pack_newest_first(ordered, tok, budget=7) == (["nine"], 7)
    kept, used = mc.pack_newest_first(ordered, tok, budget=13)
    assert kept == ["five six seven eight", "nine"] and used == 12
    kept, used = mc.pack_newest_first(ordered, tok, budget=17)
    assert kept == ["four", "five six seven eight", "nine"] and used == 14
    assert mc.pack_newest_first(ordered, tok, budget=18)[0] == ordered
    # newest-first walk stops at the first overflow even if an older one fits
    kept, _ = mc.pack_newest_first(["a", "b c d e f g h", "i"], tok, budget=9)
    assert kept == ["i"]
    assert mc.pack_newest_first([], tok) == ([], 0)
    assert mc.render_reminder([]) == ""


def test_sentence_windows():
    line = "One. Two. Three. Four. Five. Six."
    assert mc.sentence_windows(line) == ["One. Two. Three. Four.", "Five. Six."]
    assert mc.sentence_windows("One. Two.") == ["One. Two."]


def test_windows_get_unique_turns_and_no_rows_are_lost():
    from stencil.focus3 import Runtime

    d = _dialogue()
    d["sessions"][0]["text"] = (
        "Maria: " + " ".join(f"Rule {k} is always on." for k in range(6)) + "\n"
    )
    out = mc.auto_live(d, 1, Runtime(FakeClassifier()))
    assert out["admitted"] == 6 and len(out["sentences"]) == 6
    assert sorted(out["turns"]) == [1, 2]
    assert out["turns"][2] == {"session": 0, "line": 0, "window": 1}


# --------------------------------------------------------------- checker fixtures

FIXTURES = {
    "variable": {
        "regex": ".*_m$",
        "ok": "total_m = 1\ncount_m = 2\n",
        "bad": "total = 1\n",
        "stale": "total_n = 1\n",
        "literal": "x = 'total_m'\n# total_m\n",
    },
    "function": {
        "regex": ".*_fn$",
        "ok": "def add_fn(a, b):\n    return a + b\n",
        "bad": "def add(a, b):\n    return a + b\n",
        "stale": "def add_a(a, b):\n    return a + b\n",
        "literal": "def add(a, b):\n    return 'add_fn'\n",
    },
    "function argument": {
        "regex": ".*_a$",
        "ok": "def f(x_a, y_a):\n    return x_a\n",
        "bad": "def f(x, y):\n    return x\n",
        "stale": "def f(x_e, y_e):\n    return x_e\n",
        "literal": "def f(x):\n    return 'x_a'\n",
    },
    "class": {
        "regex": "^[a-z0-9_]*$",
        "ok": "class my_tree:\n    pass\n",
        "bad": "class MyTree:\n    pass\n",
        "stale": "class MYTREE:\n    pass\n",
        "literal": "class MyTree:\n    name = 'my_tree'\n",
    },
    "method": {
        "regex": ".*_md$",
        "ok": "class T:\n    def insert_md(self):\n        pass\n",
        "bad": "class T:\n    def insert(self):\n        pass\n",
        "stale": "class T:\n    def insert_a(self):\n        pass\n",
        "literal": "class T:\n    def insert(self):\n        return 'insert_md'\n",
    },
    "attribute": {
        "regex": ".*_at$",
        "ok": "class T:\n    def __init__(self):\n        self.root_at = None\n",
        "bad": "class T:\n    def __init__(self):\n        self.root = None\n",
        "stale": "class T:\n    def __init__(self):\n        self.root_i = None\n",
        "literal": "class T:\n    def __init__(self):\n        self.root = 'root_at'\n",
    },
    "function decorator": {
        "regex": ["timer", True],
        "ok": "@timer\ndef f():\n    pass\n",
        "bad": "def f():\n    pass\n",
        "stale": "@trace\ndef f():\n    pass\n",
        "literal": "def f():\n    return '@timer'\n",
    },
    "method decorator": {
        "regex": ["retry", True],
        "ok": "class T:\n    @retry\n    def m(self):\n        pass\n",
        "bad": "class T:\n    def m(self):\n        pass\n",
        "stale": "class T:\n    @validate\n    def m(self):\n        pass\n",
        "literal": "class T:\n    def m(self):\n        return '@retry'\n",
    },
    "class decorator": {
        "regex": ["timer_class", True],
        "ok": "@timer_class\nclass T:\n    pass\n",
        "bad": "class T:\n    pass\n",
        "stale": "@trace_class\nclass T:\n    pass\n",
        "literal": "class T:\n    name = '@timer_class'\n",
    },
    "import": {
        "regex": ["hashlib", True],
        "ok": "import hashlib\n\ndef f():\n    pass\n",
        "bad": "def f():\n    pass\n",
        "stale": "import gzip\n\ndef f():\n    pass\n",
        "literal": "def f():\n    return 'import hashlib'\n",
    },
    "comment": {
        "regex": True,
        "ok": "# add\ndef f():\n    pass\n",
        "bad": "def f():\n    pass\n",
        "stale": None,
        # KNOWN LIMITATION of the official checker: comments are found with
        # re.findall(r"#.*"), so a '#' inside a string literal counts as a comment.
        # Recorded in CONTRACT.md; the official checker is used unmodified.
        "literal": "def f():\n    return '# add'\n",
        "literal_counts": True,
    },
    "function annotation": {
        "regex": True,
        "ok": "def f(a: int) -> int:\n    return a\n",
        "bad": "def f(a):\n    return a\n",
        "stale": None,
        "literal": "def f(a):\n    return 'a: int'\n",
    },
    "method annotation": {
        "regex": True,
        "ok": "class T:\n    def m(self, a: int) -> int:\n        return a\n",
        "bad": "class T:\n    def m(self, a):\n        return a\n",
        "stale": None,
        "literal": "class T:\n    def m(self, a):\n        return 'a: int'\n",
    },
    "function docstring": {
        "regex": True,
        "ok": 'def f():\n    """Doc."""\n    pass\n',
        "bad": "def f():\n    pass\n",
        "stale": None,
        "literal": "def f():\n    x = 'Doc.'\n",
    },
    "method docstring": {
        "regex": True,
        "ok": 'class T:\n    def m(self):\n        """Doc."""\n        pass\n',
        "bad": "class T:\n    def m(self):\n        pass\n",
        "stale": None,
        "literal": "class T:\n    def m(self):\n        x = 'Doc.'\n",
    },
    "function assert": {
        "regex": True,
        "ok": "def f(a):\n    assert a\n    return a\n",
        "bad": "def f(a):\n    return a\n",
        "stale": None,
        "literal": "def f(a):\n    return 'assert a'\n",
    },
    "method assert": {
        "regex": True,
        "ok": "class T:\n    def m(self, a):\n        assert a\n        return a\n",
        "bad": "class T:\n    def m(self, a):\n        return a\n",
        "stale": None,
        "literal": "class T:\n    def m(self, a):\n        return 'assert a'\n",
    },
    "function try": {
        "regex": True,
        "ok": "def f(a):\n    try:\n        return a\n"
        "    except Exception:\n        pass\n",
        "bad": "def f(a):\n    return a\n",
        "stale": None,
        "literal": "def f(a):\n    return 'try:'\n",
    },
    "method try": {
        "regex": True,
        "ok": "class T:\n    def m(self, a):\n        try:\n            return a\n"
        "        except Exception:\n            pass\n",
        "bad": "class T:\n    def m(self, a):\n        return a\n",
        "stale": None,
        "literal": "class T:\n    def m(self, a):\n        return 'try:'\n",
    },
}


def _families():
    items = ROOT / "results/memorycode-derived/items.json"
    if items.exists():
        fams = set()
        for it in json.loads(items.read_text())["items"]:
            fams |= set(it["families"])
        return sorted(fams)
    return sorted(FIXTURES)


@needs_dataset
def test_every_family_in_items_has_fixtures():
    assert set(_families()) <= set(FIXTURES)


@needs_dataset
@pytest.mark.parametrize("family", sorted(FIXTURES))
def test_checker_fixture_family(family):
    compute_score = mc.vendored_checker()
    fx = FIXTURES[family]
    wrap = lambda code: f"```python\n{code}```"  # noqa: E731
    assert compute_score(wrap(fx["ok"]), family, fx["regex"]) == 1.0
    assert compute_score(wrap(fx["bad"]), family, fx["regex"]) in (0.0, None)
    if fx["stale"] is not None:
        assert compute_score(wrap(fx["stale"]), family, fx["regex"]) == 0.0
    literal = compute_score(wrap(fx["literal"]), family, fx["regex"])
    if fx.get("literal_counts"):
        assert literal == 1.0  # documented checker limitation, see FIXTURES
    else:
        assert literal in (0.0, None)
    assert compute_score(wrap("def f(:\n"), family, fx["regex"]) == 0


def test_required_families_frozen_from_query():
    fams = ["variable", "method annotation", "function", "class", "import"]
    assert mc.required_families("Binary tree class with methods", fams) == [
        "class",
        "import",
        "method annotation",
        "variable",
    ]
    assert mc.required_families("function that checks a palindrome", fams) == [
        "function",
        "import",
        "variable",
    ]
    assert mc.required_families("script that prints hello", fams) == [
        "function",
        "import",
        "variable",
    ]
    # whole-word matching: "classifies" is not a class (Astra round 4)
    assert mc.required_structure("function that classifies numbers") == ["function"]
    assert mc.required_structure("Binary tree class with methods") == ["class"]


@needs_dataset
def test_score_generation_strict_and_fraction():
    compute_score = mc.vendored_checker()
    regexes = [["variable", ".*_m$"], ["method annotation", True]]
    text = "```python\nx_m = 1\n```"
    out = mc.score_generation(text, regexes, compute_score)
    assert out["per_family"] == [1.0, None] and out["strict"] and out["fraction"] == 1.0
    # an omitted REQUIRED parent object is a failure, not "inapplicable"
    out = mc.score_generation(
        text, regexes, compute_score, required=["variable", "method annotation"]
    )
    assert out["per_family"] == [1.0, 0.0] and out["strict"] is False
    # required structure absent -> strict False even when every convention passes
    out = mc.score_generation(
        text,
        [["variable", ".*_m$"]],
        compute_score,
        required=["variable"],
        structure=["class"],
    )
    assert out["structure_present"] is False and out["strict"] is False
    out = mc.score_generation(
        "```python\nclass T:\n    x_m = 1\n```",
        [["variable", ".*_m$"]],
        compute_score,
        required=["variable"],
        structure=["class"],
    )
    assert out["structure_present"] and out["strict"] is True
    out = mc.score_generation("```python\nx = 1\n```", regexes, compute_score)
    assert out["strict"] is False and out["fraction"] == 0.0
    out = mc.score_generation("```python\nimport os\n```", regexes, compute_score)
    assert out["strict"] is None and out["fraction"] is None


@needs_dataset
def test_dataset_structure_and_split():
    ids = mc.dialogue_ids()
    assert len(ids) == 360
    d = mc.load_dialogue(ids[0])
    assert len(d["instructions"]) == len(d["sessions"])
    items = [
        {"dialogue": i // 2, "session": 1 + i % 2, "families": ["variable"]}
        for i in range(200)
    ]
    split = mc.split_items(items)
    setup = {it["dialogue"] for it in split["setup"]}
    screen = {it["dialogue"] for it in split["screen"]}
    assert len(split["setup"]) == 16 and len(split["screen"]) == 64
    assert not setup & screen
    assert split == mc.split_items(items)


@pytest.mark.skipif(not TOKENIZER.exists(), reason="local Qwen3 tokenizer")
@needs_dataset
def test_enumerate_items_respects_eligibility():
    from tokenizers import Tokenizer

    tok = Tokenizer.from_file(str(TOKENIZER))
    items = mc.enumerate_items(tok, ids=mc.dialogue_ids()[:20])
    for it in items:
        assert it["session"] >= 1 and it["history_regex"]
        assert it["history_prompt_tokens"] <= mc.MAX_PROMPT_TOKENS
        d = mc.load_dialogue(it["dialogue"])
        assert any(mc.has_instruction(d["sessions"][i]) for i in range(it["session"]))


# ------------------------------------------------------------- Exp 4 LONG cohort


def test_split_long_is_deterministic_and_disjoint():
    items = [{"dialogue": i, "session": 2} for i in range(212)]
    split = mc.split_long(items)
    setup = {it["dialogue"] for it in split["setup_long"]}
    screen = {it["dialogue"] for it in split["screen_long"]}
    assert len(setup) == 16 and len(screen) == 128 and not setup & screen
    assert split["reserve"] == 68
    assert split == mc.split_long(items)


def test_output_failures_columns():
    ok = "```python\ndef f():\n    return 1\n```"
    bad = "```python\ndef f(:\n```"
    assert mc.output_failures(ok, list(range(20)), False) == {
        "invalid": False,
        "truncated": False,
        "degenerate": False,
        "timed_out": False,
        "repetition_4gram": 0.0,
    }
    assert mc.output_failures(bad, [1, 2, 3, 4] * 10, True)["invalid"] is True
    assert mc.output_failures(ok, [1, 2, 3, 4] * 10, True)["degenerate"] is True
    assert mc.output_failures("", [], False)["invalid"] is True


@pytest.mark.skipif(not TOKENIZER.exists(), reason="local Qwen3 tokenizer")
@needs_dataset
def test_long_prompt_lengths_match_between_arms():
    from tokenizers import Tokenizer

    tok = Tokenizer.from_file(str(TOKENIZER))
    listing = ROOT / "results/memorycode-long/items.json"
    if listing.exists():
        item = json.loads(listing.read_text())["items"][0]
    else:
        items = mc.long_items(tok)
        assert items, "no long item in the dataset"
        item = items[0]
    d = mc.load_dialogue(item["dialogue"])
    query = item["queries"][0]
    base = mc.build_long_prompt(d, item["session"], query, tok, "")
    sentences = mc.oracle_sentences(d, item["session"], mc.load_topics()) or [
        "always end variable names with '_m'."
    ]
    reminder = mc.render_long_reminder(mc.pack_long(sentences, tok)[0])
    focus = mc.build_long_prompt(d, item["session"], query, tok, reminder)
    assert base["prompt_tokens"] <= mc.WINDOW and focus["prompt_tokens"] <= mc.WINDOW
    assert abs(base["prompt_tokens"] - focus["prompt_tokens"]) <= 2
    assert focus["thread_tokens_kept"] < base["thread_tokens_kept"]
    assert mc.LONG_HEADER in focus["prompt"] and mc.LONG_HEADER not in base["prompt"]
    assert focus["prompt"].endswith(mc.OPENER)
    # the window keeps the NEWEST text: the current session's request is present
    assert d["sessions"][item["session"]]["text"][-60:] in base["prompt"]


@pytest.mark.skipif(not TOKENIZER.exists(), reason="local Qwen3 tokenizer")
@needs_dataset
def test_evicted_mentor_sentences_are_outside_the_window():
    from tokenizers import Tokenizer

    tok = Tokenizer.from_file(str(TOKENIZER))
    item = json.loads((ROOT / "results/memorycode-long/items.json").read_text())[
        "items"
    ][0]
    d = mc.load_dialogue(item["dialogue"])
    base = mc.build_long_prompt(d, item["session"], item["queries"][0], tok, "")
    head = base["prompt"].index(":\n") + 2
    kept = base["prompt"][head : base["prompt"].index(" \nBased on")]
    evicted = mc.evicted_mentor_sentences(d, item["session"], kept)
    # the metadata path (cut_chars) gives the same answer as the legacy text path
    assert kept == base["thread_text_kept"]
    assert evicted == mc.evicted_mentor_sentences(
        d, item["session"], cut=base["cut_chars"]
    )
    assert evicted, "a LONG item must have mentor sentences outside the window"
    everything = [c["text"] for c in mc.mentor_sentences(d, item["session"])]
    assert set(evicted) <= set(everything) and len(evicted) < len(everything)
    # session 0 lies entirely outside the window of a LONG item
    first = [c["text"] for c in mc.mentor_sentences(d, 1)]
    assert first and first[0] == evicted[0]


def test_timeout_is_a_failure_column():
    f = mc.output_failures("```python\nx = 1\n```", [1, 2, 3], False, timed_out=True)
    assert f["timed_out"] and mc.any_failure(f)
    assert not mc.any_failure(
        {"invalid": False, "truncated": False, "degenerate": False}
    )


def test_evicted_rule_ignores_embedded_request_marker():
    """The cut comes from build_long_prompt metadata, not from rediscovering the
    ' \nBased on' marker, so a conversation containing that marker is sliced
    correctly (Astra Exp 4 implementation review, finding 8)."""
    from tokenizers import Tokenizer

    tok = Tokenizer.from_file(str(TOKENIZER))
    item = json.loads((ROOT / "results/memorycode-long/items.json").read_text())[
        "items"
    ][0]
    d = copy.deepcopy(mc.load_dialogue(item["dialogue"]))
    s = item["session"]
    mentor = d["context"]["mentor"]
    # plant the marker inside the NEWEST session (retained by the window)
    d["sessions"][s]["text"] += f"\n{mentor}: Remember this. \nBased on nothing."
    base = mc.build_long_prompt(d, s, item["queries"][0], tok, "")
    assert base["prompt"].count(" \nBased on") == 2
    evicted = mc.evicted_mentor_sentences(d, s, cut=base["cut_chars"])
    assert "Remember this." not in evicted
    # legacy marker slicing would have shortened the kept text and shifted the cut
    head = base["prompt"].index(":\n") + 2
    sliced = base["prompt"][head : base["prompt"].index(" \nBased on")]
    assert len(sliced) < len(base["thread_text_kept"])


def test_long_prompts_equal_on_every_frozen_item():
    """Paired equality over the whole frozen cohort, both primary arms, and the
    window fit (finding 9); CPU only."""
    from tokenizers import Tokenizer

    tok = Tokenizer.from_file(str(TOKENIZER))
    items = [
        it
        for it in json.loads((ROOT / "results/memorycode-long/items.json").read_text())[
            "items"
        ]
        if it["split"] != "reserve"
    ]
    assert len(items) == 144
    unequal = []
    for it in items:
        d = mc.load_dialogue(it["dialogue"])
        base = mc.build_long_prompt(d, it["session"], it["queries"][0], tok, "")
        evicted = mc.evicted_mentor_sentences(d, it["session"], cut=base["cut_chars"])
        kept, used = mc.pack_long(evicted, tok)
        assert used <= mc.BUDGET
        focus = mc.build_long_prompt(
            d, it["session"], it["queries"][0], tok, mc.render_long_reminder(kept)
        )
        assert base["prompt_tokens"] <= mc.WINDOW >= focus["prompt_tokens"]
        if base["prompt_tokens"] != focus["prompt_tokens"]:
            unequal.append(it["id"])
    assert unequal == []


def _fake_long_record(
    item,
    base_ok,
    focus_ok,
    oracle_ok=None,
    timed_out=False,
    model="1.7b",
    seconds=10.0,
    manifest=True,
):
    """Synthetic LONG record with the manifest and terminal scored generation the
    summary consumer validates (Exp 4B review finding 4). ``ok`` = every required
    check passes (fraction_required 1.0), else none (0.0)."""
    query = item.get("queries", [None])[0]
    required = set(item.get("required", {}).get(query, []))

    def arm(ok):
        per_family = [
            (1.0 if ok else 0.0) if str(obj) in required else None
            for obj, _r in item.get("history_regex", [])
        ]
        return {
            "policy": None,
            "selected_sentences": 0,
            "kept_sentences": 0,
            "reminder": "",
            "reminder_tokens": 0,
            "reminder_empty": True,
            "generations": [
                {
                    "query": query,
                    "window": {"prompt_tokens": 3584},
                    "timed_out": timed_out,
                    "termination": "timeout" if timed_out else "eos",
                    "seconds": seconds,
                    "failures": {
                        "invalid": False,
                        "truncated": False,
                        "degenerate": False,
                        "timed_out": timed_out,
                    },
                    "scores": {
                        "per_family": per_family,
                        "structure_present": True,
                        "strict": ok and not timed_out,
                        "fraction": 1.0 if ok else 0.0,
                        "fraction_required": (
                            0.0 if timed_out else (1.0 if ok else 0.0)
                        ),
                    },
                }
            ],
            "strict": ok and not timed_out,
            "fraction": 1.0 if ok else 0.0,
        }

    arms = {"base": arm(base_ok), "focus": arm(focus_ok)}
    if oracle_ok is not None:
        arms["oracle"] = arm(oracle_ok)
    rec = {"id": item["id"], "split": item["split"], "model": model, "arms": arms}
    if manifest:
        rec["manifest"] = {
            "model": model,
            "window": mc.WINDOW,
            "budget_tokens": mc.BUDGET,
            "policy": "role_evicted",
        }
    return rec


def test_long_summary_consumer(tmp_path, monkeypatch):
    """The actual LONG summary consumer on synthetic records: no crash, INCOMPLETE
    when a frozen primary item is missing, records without oracle kept, and the
    confirmatory reading only for screen_long/role_evicted (findings 2-3)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "memorycode_screen", ROOT / "scripts/memorycode_screen.py"
    )
    screen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(screen)
    items = [
        it
        for it in json.loads((ROOT / "results/memorycode-long/items.json").read_text())[
            "items"
        ]
        if it["split"] == "screen_long"
    ]
    root = tmp_path / "long"
    root.mkdir()
    (root / "items.json").write_text(json.dumps({"items": items}))
    out = root / "screen_long-role_evicted"
    out.mkdir()
    monkeypatch.setattr(screen, "OUT_LONG", root)

    class Args:
        cohort = "long"
        split = "screen_long"
        model = "1.7b"
        policy = "role_evicted"

    # incomplete: 10 of 128 items, focus wins every time, some without oracle
    for i, it in enumerate(items[:10]):
        rec = _fake_long_record(it, False, True, oracle_ok=True if i % 2 else None)
        (out / f"item-{it['id']}.json").write_text(json.dumps(rec))
    summary = screen.phase_summarize(Args())
    assert summary["items_complete"] == 10 and not summary["primary_complete"]
    assert summary["reading"]["verdict"] == "INCOMPLETE"
    assert summary["items_with_arm"]["oracle"] == 5
    assert len(summary["missing_primary_ids"]) == 118
    # complete, all focus wins -> PROVEN only on the registered split/policy
    for it in items[10:]:
        rec = _fake_long_record(it, False, True)
        (out / f"item-{it['id']}.json").write_text(json.dumps(rec))
    summary = screen.phase_summarize(Args())
    assert summary["primary_complete"] and summary["reading"]["verdict"] == "PROVEN"
    assert summary["reading"]["n_primary"] == 128
    assert summary["contrasts"]["oracle_vs_focus"]["paired_interval"]["n"] == 5

    # ---- Exp 4B review cases ------------------------------------------------
    class Args4B(Args):
        model = "4b"
        primary = "fraction"

    out4 = root / "screen_long-4b-role_evicted"
    out4.mkdir()
    # (finding 2) complete SCREEN with ZERO oracle records must not crash and reads
    # PROVEN on the fraction primary for the 4B trunk
    for it in items:
        (out4 / f"item-{it['id']}.json").write_text(
            json.dumps(_fake_long_record(it, False, True, model="4b"))
        )
    summary = screen.phase_summarize(Args4B())
    assert summary["items_with_arm"]["oracle"] == 0
    assert (
        summary["contrasts"]["oracle_vs_base"]["fraction_required_bootstrap"]["n"] == 0
    )
    assert summary["reading"]["verdict"] == "PROVEN"
    assert summary["reading"]["n_primary"] == 128
    assert summary["reading"]["lower_points"] > 0
    # (finding 4) the same records labelled 1.7B are invalid for a 4B summary
    bad = _fake_long_record(items[0], False, True, model="1.7b")
    (out4 / f"item-{items[0]['id']}.json").write_text(json.dumps(bad))
    summary = screen.phase_summarize(Args4B())
    assert items[0]["id"] in summary["invalid_record_ids"]
    assert not summary["primary_complete"]
    assert summary["reading"]["verdict"] == "INCOMPLETE"
    # a 1.7B SCREEN on the fraction primary is never confirmatory (DESCRIPTIVE)
    (out4 / f"item-{items[0]['id']}.json").write_text(
        json.dumps(_fake_long_record(items[0], False, True, model="4b"))
    )

    class Args17(Args4B):
        model = "1.7b"

    out17 = root / "screen_long-role_evicted"
    for it in items:
        (out17 / f"item-{it['id']}.json").write_text(
            json.dumps(_fake_long_record(it, False, True))
        )
    assert screen.phase_summarize(Args17())["reading"]["verdict"] == "DESCRIPTIVE"
    # (finding 5) a compliant generation that timed out scores 0.0 on the primary
    rec = _fake_long_record(items[1], True, True, model="4b", timed_out=True)
    rec["arms"]["focus"]["generations"][0]["scores"]["fraction_required"] = 1.0
    assert screen._required_fraction_of(rec, "focus", items[1]) == 0.0

    # (finding 6) budget exhaustion across chunks -> INCOMPLETE even when complete
    class Ceiling(Args4B):
        ceiling_seconds = 128 * 2 * 10.0 - 1  # records carry 10 s each

    summary = screen.phase_summarize(Ceiling())
    assert summary["budget"]["exhausted"] and not summary["primary_complete"]
    assert summary["reading"]["verdict"] == "INCOMPLETE"
    (out4 / "BUDGET_EXHAUSTED.json").write_text(json.dumps({"marker": True}))
    summary = screen.phase_summarize(Args4B())
    assert summary["budget"]["exhausted"]
    assert summary["reading"]["verdict"] == "INCOMPLETE"
    (out4 / "BUDGET_EXHAUSTED.json").unlink()
    assert screen.phase_summarize(Args4B())["reading"]["verdict"] == "PROVEN"

    class Setup(Args):
        split = "setup_long"
        policy = "register"

    setup_items = [
        it
        for it in json.loads((ROOT / "results/memorycode-long/items.json").read_text())[
            "items"
        ]
        if it["split"] == "setup_long"
    ]
    (root / "items.json").write_text(json.dumps({"items": items + setup_items}))
    sdir = root / "setup_long"
    sdir.mkdir()
    for it in setup_items:
        (sdir / f"item-{it['id']}.json").write_text(
            json.dumps(_fake_long_record(it, False, True, oracle_ok=True))
        )
    summary = screen.phase_summarize(Setup())
    assert summary["primary_complete"]
    assert summary["reading"]["verdict"] == "DESCRIPTIVE"

    # (finding 3) qualification object on SETUP-LONG 4B, fraction primary
    class Qual(Setup):
        model = "4b"
        policy = "role_evicted"
        primary = "fraction"

    qdir = root / "setup_long-4b-role_evicted"
    qdir.mkdir()
    # 16 base/focus pairs but only ONE oracle record: INCOMPLETE, never a pass
    for i, it in enumerate(setup_items):
        (qdir / f"item-{it['id']}.json").write_text(
            json.dumps(
                _fake_long_record(
                    it, False, True, oracle_ok=True if i == 0 else None, model="4b"
                )
            )
        )
    q = screen.phase_summarize(Qual())["qualification"]
    assert q["status"] == "INCOMPLETE" and q["passed"] is None
    assert len(q["missing_three_arm_ids"]) == 15
    # complete with oracle applying everything and focus winning: PASSED
    for it in setup_items:
        (qdir / f"item-{it['id']}.json").write_text(
            json.dumps(_fake_long_record(it, False, True, oracle_ok=True, model="4b"))
        )
    q = screen.phase_summarize(Qual())["qualification"]
    assert q["status"] == "PASSED" and all(q["conditions"].values())
    # oracle floor (all zero) fails condition (a); focus harm fails (c)
    for it in setup_items:
        (qdir / f"item-{it['id']}.json").write_text(
            json.dumps(_fake_long_record(it, True, False, oracle_ok=False, model="4b"))
        )
    q = screen.phase_summarize(Qual())["qualification"]
    assert q["status"] == "FAILED"
    assert not q["conditions"]["oracle_mean_fraction_required_ge_0.20"]
    assert not q["conditions"]["focus_minus_base_upper_gt_0"]


def test_failure_excess_reports_both_directions():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "memorycode_screen", ROOT / "scripts/memorycode_screen.py"
    )
    screen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(screen)
    items = [{"id": f"x-{i}", "split": "screen_long"} for i in range(10)]
    recs = []
    for i, it in enumerate(items):
        rec = _fake_long_record(it, True, True)
        # 3 focus-only failures, 2 base-only failures
        if i < 3:
            rec["arms"]["focus"]["generations"][0]["failures"]["invalid"] = True
        elif i < 5:
            rec["arms"]["base"]["generations"][0]["failures"]["truncated"] = True
        recs.append(rec)
    out = screen._failure_excess(recs, ["base", "focus"], "base")
    assert (
        out["focus"]["excess_items"] == 3 and out["focus"]["reference_only_items"] == 2
    )
    assert out["focus"]["net_rate_difference"] == pytest.approx(0.1)
    assert out["focus"]["categories"]["invalid"] == 3
    assert out["base"]["excess_items"] == 0  # reference vs itself


def test_fraction_required_has_a_frozen_denominator():
    """Exp 4B primary: the denominator is the query's REQUIRED families; optional
    families an output introduces are ignored; missing structure scores 0.0;
    a query that requires nothing is inapplicable (None)."""
    regexes = [["variable", ".*_m$"], ["method annotation", True], ["class", True]]
    # required = variable + method annotation; class is optional and ignored
    scores = [1.0, 0.0, 1.0]
    assert mc.fraction_required(
        scores, regexes, ["variable", "method annotation"], True
    ) == pytest.approx(0.5)
    # an optional family failing does not move the score
    assert mc.fraction_required([1.0, 1.0, 0.0], regexes, ["variable"], True) == 1.0
    # an absent required parent (None) counts 0.0
    assert mc.fraction_required([None, 1.0, None], regexes, ["variable"], True) == 0.0
    # missing required structure -> 0.0 whatever the conventions score
    assert mc.fraction_required([1.0, 1.0, 1.0], regexes, ["variable"], False) == 0.0
    # nothing required -> inapplicable
    assert mc.fraction_required([1.0, 1.0, 1.0], regexes, [], True) is None
    assert mc.fraction_required([1.0, 1.0, 1.0], regexes, None, True) is None
    # a family with several checks contributes each check (equal weight per check)
    twice = [["variable", ".*_m$"], ["variable", "^[a-z]"], ["class", True]]
    assert mc.fraction_required([1.0, 0.0, 1.0], twice, ["variable"], True) == 0.5
    # malformed input raises instead of silently truncating (review finding 1)
    with pytest.raises(ValueError):
        mc.fraction_required([1.0], regexes, ["variable"], True)
    with pytest.raises(ValueError):
        mc.fraction_required([1.0, 1.0, 1.0], regexes, ["function"], True)
    # score_generation carries the field
    out = mc.score_generation(
        "```python\nx_m = 1\n```",
        [["variable", ".*_m$"], ["method annotation", True]],
        mc.vendored_checker(),
        required=["variable", "method annotation"],
    )
    assert out["fraction_required"] == pytest.approx(0.5)


def test_paired_mean_bootstrap_is_deterministic_and_reads_direction():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "memorycode_screen", ROOT / "scripts/memorycode_screen.py"
    )
    screen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(screen)
    a = [0.5, 0.75, 1.0, 0.25, 0.5, 0.5, 1.0, 0.0]
    b = [0.25, 0.5, 0.5, 0.25, 0.0, 0.5, 0.5, 0.0]
    one = screen._paired_mean_bootstrap(a, b, draws=2000)
    two = screen._paired_mean_bootstrap(a, b, draws=2000)
    assert one == two  # seed 0 fixed
    assert (
        one["n"] == 8 and one["wins"] == 5 and one["losses"] == 0 and one["ties"] == 3
    )
    assert one["mean_points"] == pytest.approx(100 * (sum(a) - sum(b)) / 8)
    assert one["lower_points"] > 0 and one["upper_points"] >= one["mean_points"]
    assert one["sign_p_two_sided"] == pytest.approx(2 * 0.5**5)
    flipped = screen._paired_mean_bootstrap(b, a, draws=2000)
    assert flipped["upper_points"] < 0 and flipped["losses"] == 5

    # fraction_reading verdict ladder on a synthetic summary
    empty = screen._paired_mean_bootstrap([], [], draws=100)
    assert empty["n"] == 0 and empty["lower_points"] is None
    with pytest.raises(ValueError):
        screen._paired_mean_bootstrap([1.0], [], draws=100)

    def summary(lower, upper, excess, complete=True, split="screen_long", model="4b"):
        return {
            "split": split,
            "model": model,
            "policy": "role_evicted",
            "primary_complete": complete,
            "items_expected": 128,
            "contrasts": {
                "focus_vs_base": {
                    "fraction_required_bootstrap": {
                        "n": 128,
                        "mean_points": (lower + upper) / 2,
                        "lower_points": lower,
                        "upper_points": upper,
                    }
                }
            },
            "output_failure_excess_over_base": {"focus": {"excess_fraction": excess}},
        }

    assert screen.fraction_reading(summary(1.0, 5.0, 0.02))["verdict"] == "PROVEN"
    assert (
        screen.fraction_reading(summary(1.0, 5.0, 0.08))["verdict"]
        == "POSITIVE-WITH-OUTPUT-FAILURE-EXCESS"
    )
    assert screen.fraction_reading(summary(-1.0, 5.0, 0.0))["verdict"] == "NOT PROVEN"
    assert screen.fraction_reading(summary(-6.0, -1.0, 0.0))["verdict"] == "HARM"
    assert (
        screen.fraction_reading(summary(1.0, 5.0, 0.0, complete=False))["verdict"]
        == "INCOMPLETE"
    )
    assert (
        screen.fraction_reading(summary(1.0, 5.0, 0.0, split="setup_long"))["verdict"]
        == "DESCRIPTIVE"
    )
    assert (
        screen.fraction_reading(summary(1.0, 5.0, 0.0, model="1.7b"))["verdict"]
        == "DESCRIPTIVE"
    )
