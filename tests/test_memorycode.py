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
        "instructions": [[[12, 5]], [[12, 5]], [[12, 5], [17, 0]]],
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
            {"id": 12, "text": ["a", "b", "c", "d", "e", "with _n"]},
            {"id": 17, "text": ["annotations"]},
        ]
    }
    assert mc.oracle_sentences(_dialogue(), 2, topics) == ["with _n", "annotations"]


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
    assert evicted, "a LONG item must have mentor sentences outside the window"
    everything = [c["text"] for c in mc.mentor_sentences(d, item["session"])]
    assert set(evicted) <= set(everything) and len(evicted) < len(everything)
    # session 0 lies entirely outside the window of a LONG item
    first = [c["text"] for c in mc.mentor_sentences(d, 1)]
    assert first and first[0] == evicted[0]
