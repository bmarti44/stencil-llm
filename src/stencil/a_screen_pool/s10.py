# ruff: noqa: E501
"""S10: podcast feeds — naming (target, replacement) x error_surface=wrap (support)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '"""podshelf package."""\n'

_MODEL = '''"""Feed records and the package error."""

from dataclasses import dataclass, replace


class PodshelfError(Exception):
    """Anything that failed underneath FeedStore's public API."""


@dataclass(frozen=True)
class Feed:
    feed_id: str
    title: str
    url: str
    episodes: tuple[str, ...] = ()

    def with_episodes(self, episodes: tuple[str, ...]) -> "Feed":
        return replace(self, episodes=episodes)
'''

_SOURCE = '''"""Feed documents: reading files and parsing the minimal 'episode:' text format."""

from pathlib import Path


def read_document(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def parse_document(text: str) -> list[str]:
    titles = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition(":")
        if key.strip() != "episode" or not sep or not value.strip():
            raise ValueError(f"bad feed line: {raw!r}")
        titles.append(value.strip())
    return titles
'''

_STORE = '''"""In-memory feed store."""

from podshelf.model import Feed


class FeedStore:
    def __init__(self) -> None:
        self._feeds: dict[str, Feed] = {}
        self._counter = 0

    def add_feed(self, title: str, url: str) -> Feed:
        self._counter += 1
        feed = Feed(feed_id=f"F{self._counter}", title=title, url=url)
        self._feeds[feed.feed_id] = feed
        return feed

    def find(self, feed_id: str) -> Feed | None:
        return self._feeds.get(feed_id)

    def count(self) -> int:
        return len(self._feeds)
'''

_FILES = {
    "podshelf/__init__.py": _INIT,
    "podshelf/model.py": _MODEL,
    "podshelf/source.py": _SOURCE,
    "podshelf/store.py": _STORE,
}

_DOC = (
    "# weekly\\nepisode: Pilot\\nepisode: The Second One\\n\\nepisode: Listener Mail\\n"
)

# ----------------------------------------------------------------- checkpoint 1: refresh from text

_C1_HELPER = f"""import pytest

from podshelf.model import PodshelfError
from podshelf.store import FeedStore

DOC = "{_DOC}"


def _refresh(store):
    fn = getattr(store, "refresh_feed", None) or getattr(store, "feed_refresh", None)
    assert fn is not None, "no refresh method found"
    return fn
"""

_C1_FUNCTIONAL = {
    "test_refresh_functional.py": _C1_HELPER
    + """

def test_refresh_parses_titles_in_order():
    s = FeedStore()
    f = s.add_feed("Weekly", "https://example.test/weekly.txt")
    out = _refresh(s)(f.feed_id, DOC)
    assert out.episodes == ("Pilot", "The Second One", "Listener Mail")
    assert s.find(f.feed_id).episodes == out.episodes


def test_refresh_replaces_previous_episodes():
    s = FeedStore()
    f = s.add_feed("Weekly", "u")
    _refresh(s)(f.feed_id, DOC)
    out = _refresh(s)(f.feed_id, "episode: Only\\n")
    assert out.episodes == ("Only",)


def test_refresh_keeps_title_url_and_id():
    s = FeedStore()
    f = s.add_feed("Weekly", "u")
    out = _refresh(s)(f.feed_id, DOC)
    assert out.feed_id == f.feed_id and out.title == "Weekly" and out.url == "u"


def test_refresh_unknown_feed_raises_keyerror():
    s = FeedStore()
    with pytest.raises(KeyError):
        _refresh(s)("F9", DOC)


def test_refresh_bad_document_leaves_feed_untouched():
    s = FeedStore()
    f = s.add_feed("Weekly", "u")
    _refresh(s)(f.feed_id, "episode: Pilot\\n")
    with pytest.raises(Exception):
        _refresh(s)(f.feed_id, "episode: Pilot\\ntitle: oops\\n")
    assert s.find(f.feed_id).episodes == ("Pilot",)
"""
}

_C1_REGRESSION = {
    "test_refresh_regression.py": """import pytest

from podshelf.source import parse_document
from podshelf.store import FeedStore


def test_add_find_count_unchanged():
    s = FeedStore()
    f = s.add_feed("Weekly", "u")
    assert f.feed_id == "F1" and f.episodes == ()
    assert s.find("F1") is f and s.find("F2") is None
    assert s.count() == 1


def test_parse_document_unchanged():
    assert parse_document("# c\\nepisode: A\\n\\nepisode: B\\n") == ["A", "B"]
    with pytest.raises(ValueError):
        parse_document("episode:\\n")
"""
}

_C1_CONTRACT = {
    "verb_noun": {
        "test_refresh_naming.py": """from podshelf.store import FeedStore


def test_refresh_is_verb_noun():
    assert hasattr(FeedStore, "refresh_feed")
    assert not hasattr(FeedStore, "feed_refresh")
"""
    },
    "noun_verb": {
        "test_refresh_naming.py": """from podshelf.store import FeedStore


def test_refresh_is_noun_verb():
    assert hasattr(FeedStore, "feed_refresh")
    assert not hasattr(FeedStore, "refresh_feed")
"""
    },
}

_C1_SUPPORT = {
    "test_refresh_errors.py": _C1_HELPER
    + """

def test_parse_failure_is_wrapped_in_package_error():
    s = FeedStore()
    f = s.add_feed("Weekly", "u")
    with pytest.raises(PodshelfError) as info:
        _refresh(s)(f.feed_id, "episode: Pilot\\nbogus line\\n")
    assert not isinstance(info.value, ValueError)
    assert isinstance(info.value.__cause__, ValueError)
"""
}


def _gold1(name: str) -> str:
    return (
        _STORE.replace(
            "from podshelf.model import Feed\n",
            "from podshelf.model import Feed, PodshelfError\n"
            "from podshelf.source import parse_document\n",
            1,
        ).rstrip("\n")
        + f"""

    def {name}(self, feed_id: str, text: str) -> Feed:
        feed = self._feeds[feed_id]
        try:
            titles = parse_document(text)
        except ValueError as exc:
            raise PodshelfError(f"feed {{feed_id}}: {{exc}}") from exc
        refreshed = feed.with_episodes(tuple(titles))
        self._feeds[feed_id] = refreshed
        return refreshed
"""
    )


_REQ1 = Request(
    text=(
        "Add a public method on FeedStore that refreshes a feed from a document: it "
        "takes the feed id and the document text, parses the episode titles with "
        "parse_document from source.py, replaces the feed's episodes with those titles "
        "(as a tuple, in document order), stores the updated feed and returns it. An "
        "unknown id raises KeyError. A document that does not parse must leave the feed "
        "untouched."
    ),
    target="podshelf/store.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold={"verb_noun": _gold1("refresh_feed"), "noun_verb": _gold1("feed_refresh")},
)

# ----------------------------------------------------------------- checkpoint 2: load from a file

_C2_HELPER = f"""import pytest

from podshelf.model import PodshelfError
from podshelf.store import FeedStore

DOC = "{_DOC}"


def _load(store):
    fn = getattr(store, "load_feed", None) or getattr(store, "feed_load", None)
    assert fn is not None, "no load method found"
    return fn
"""

_C2_FUNCTIONAL = {
    "test_load_functional.py": _C2_HELPER
    + """

def test_load_reads_file_and_refreshes(tmp_path):
    p = tmp_path / "weekly.txt"
    p.write_text(DOC, encoding="utf-8")
    s = FeedStore()
    f = s.add_feed("Weekly", "u")
    out = _load(s)(f.feed_id, str(p))
    assert out.episodes == ("Pilot", "The Second One", "Listener Mail")
    assert s.find(f.feed_id).episodes == out.episodes


def test_load_replaces_previous_episodes(tmp_path):
    p = tmp_path / "w.txt"
    p.write_text("episode: Only\\n", encoding="utf-8")
    s = FeedStore()
    f = s.add_feed("Weekly", "u")
    _load(s)(f.feed_id, str(p))
    p.write_text("episode: A\\nepisode: B\\n", encoding="utf-8")
    assert _load(s)(f.feed_id, str(p)).episodes == ("A", "B")


def test_load_unknown_feed_raises_keyerror(tmp_path):
    p = tmp_path / "w.txt"
    p.write_text(DOC, encoding="utf-8")
    s = FeedStore()
    with pytest.raises(KeyError):
        _load(s)("F9", str(p))


def test_load_missing_file_leaves_feed_untouched(tmp_path):
    s = FeedStore()
    f = s.add_feed("Weekly", "u")
    with pytest.raises(Exception):
        _load(s)(f.feed_id, str(tmp_path / "absent.txt"))
    assert s.find(f.feed_id).episodes == ()
"""
}

_C2_REGRESSION = {
    "test_load_regression.py": """from podshelf.store import FeedStore


def _refresh(store):
    return getattr(store, "refresh_feed", None) or getattr(store, "feed_refresh", None)


def test_add_find_refresh_unchanged():
    s = FeedStore()
    f = s.add_feed("Weekly", "u")
    assert s.find("F1") is f and s.count() == 1
    assert _refresh(s)("F1", "episode: Pilot\\n").episodes == ("Pilot",)
"""
}

_C2_CONTRACT = {
    "verb_noun": {
        "test_load_naming.py": """from podshelf.store import FeedStore


def test_load_is_verb_noun():
    assert hasattr(FeedStore, "load_feed")
    assert not hasattr(FeedStore, "feed_load")
"""
    },
    "noun_verb": {
        "test_load_naming.py": """from podshelf.store import FeedStore


def test_load_is_noun_verb():
    assert hasattr(FeedStore, "feed_load")
    assert not hasattr(FeedStore, "load_feed")
"""
    },
}

_C2_SUPPORT = {
    "test_load_errors.py": _C2_HELPER
    + """

def test_missing_file_is_wrapped_in_package_error(tmp_path):
    s = FeedStore()
    f = s.add_feed("Weekly", "u")
    with pytest.raises(PodshelfError) as info:
        _load(s)(f.feed_id, str(tmp_path / "absent.txt"))
    assert not isinstance(info.value, OSError)
    assert isinstance(info.value.__cause__, OSError)


def test_bad_file_content_is_wrapped_in_package_error(tmp_path):
    p = tmp_path / "w.txt"
    p.write_text("episode: A\\nnot a field\\n", encoding="utf-8")
    s = FeedStore()
    f = s.add_feed("Weekly", "u")
    with pytest.raises(PodshelfError):
        _load(s)(f.feed_id, str(p))
"""
}


def _gold2(name: str) -> str:
    # Built on the checkpoint-1 gold under the state then in force (verb_noun).
    return (
        _gold1("refresh_feed")
        .replace(
            "from podshelf.source import parse_document\n",
            "from podshelf.source import parse_document, read_document\n",
            1,
        )
        .rstrip("\n")
        + f"""

    def {name}(self, feed_id: str, path: str) -> Feed:
        try:
            text = read_document(path)
        except OSError as exc:
            raise PodshelfError(f"cannot read {{path}}: {{exc}}") from exc
        return self.refresh_feed(feed_id, text)
"""
    )


_REQ2 = Request(
    text=(
        "Add a public method on FeedStore that loads a feed from a file: it takes the "
        "feed id and a file path, reads the document with read_document from source.py, "
        "and refreshes the feed from that text through the existing refresh method, "
        "returning the updated feed. An unknown id raises KeyError. A file that cannot "
        "be read, or that does not parse, must leave the feed untouched."
    ),
    target="podshelf/store.py",
    functional_tests=_C2_FUNCTIONAL,
    regression_tests=_C2_REGRESSION,
    contract_tests=_C2_CONTRACT,
    support_tests=_C2_SUPPORT,
    gold={"verb_noun": _gold2("load_feed"), "noun_verb": _gold2("feed_load")},
)

# ----------------------------------------------------------------- prefix (16 turns)

_PREFIX = [
    Turn(
        "user",
        "I want to stop using a podcast app that keeps reordering my queue and instead "
        "keep my subscriptions in a tiny package, podshelf, that a script on my NAS "
        "refreshes nightly and turns into a static page. The feeds get mirrored by a "
        "separate fetcher into plain text files, one per feed, in a format I control "
        "because real RSS is a swamp:\n\n```\n# fetched 2026-09-12 02:00\nepisode: The "
        "Long Way Round\nepisode: Interview With A Lighthouse Keeper\nepisode: Mailbag "
        "#41\n```\n\nSo podshelf never touches the network: it reads those files, keeps "
        "Feed records in a FeedStore, and the page script asks it questions. Around "
        "sixty feeds, a few hundred episode titles. Could you draft the README scope so "
        "it is clear this is not a podcast client, and mention that the text format is "
        "the only input we promise to keep stable?",
    ),
    Turn(
        "assistant",
        "Here is a scope section that makes the boundary explicit:\n\n```\n## Scope\n"
        "podshelf is an in-memory subscription shelf for a single process. It keeps "
        "Feed records in a FeedStore and reads mirrored feed documents in the "
        "`episode:` text format. It is a library for scripts and tests: no networking, "
        "no audio, no playback state, no persistence beyond what your script writes.\n\n"
        "## Stable input\nThe mirrored document (`episode: <title>` per line, `#` "
        "comments, blank lines ignored) is the only input format we promise to keep.\n\n"
        "## Non-goals\n- fetching RSS or Atom\n- downloading or playing audio\n- a "
        "queue or listening history\n```\n\nSplitting 'stable input' out of scope is "
        "useful because the fetcher is a different program with its own release "
        "cadence; this section is the contract between them. A usage snippet for the "
        "README, so the page script author sees the shape of the API before reading "
        "code:\n\n```python\nfrom podshelf.store import FeedStore\n\nstore = FeedStore()\n"
        'weekly = store.add_feed("The Weekly", "https://example.test/weekly.xml")\n'
        "print(weekly.feed_id, weekly.episodes)  # F1 ()\n```\n\nThe `url` field is kept "
        "on Feed even though podshelf never fetches it, because the page links to the "
        "original feed and the fetcher's configuration is the wrong place to look it up "
        "from a template.",
    ),
    Turn(
        "user",
        "Good. I wrote `parse_document` in source.py. It skips blanks and `#` lines and "
        "raises ValueError on any other line that is not `episode: something`. My "
        "worry is that one bad line in a sixty-feed refresh kills the whole night. "
        "Should the parser skip lines it does not understand and carry on? Here is my "
        "test draft:\n\n```python\nimport pytest\n\nfrom podshelf.source import "
        "parse_document\n\n\ndef test_parse_keeps_order_and_skips_noise():\n    text = "
        '"# x\\nepisode: A\\n\\n  episode:  B  \\n"\n    assert parse_document(text) == '
        '["A", "B"]\n\n\n@pytest.mark.parametrize("line", ["title: A", "episode:", '
        '"episode A", "A"])\ndef test_parse_rejects_bad_line(line):\n    with '
        'pytest.raises(ValueError):\n        parse_document(f"episode: ok\\n{line}\\n")\n'
        "```",
    ),
    Turn(
        "assistant",
        "Keep the parser strict and put the tolerance one level up. A parser that skips "
        "what it does not understand hides fetcher bugs: the night the fetcher starts "
        "writing `title:` instead of `episode:` you would get sixty silently empty feeds "
        "and no error. The refresh script can catch per feed, log it, and keep going, "
        "which gives you both a complete night and a visible failure. Your tests are "
        "right; add one for a document that is only comments and blanks returning `[]`, "
        "because that is the real 'feed went quiet' case and it must not raise:\n\n"
        "```python\ndef test_parse_empty_document_is_empty_list():\n    assert "
        'parse_document("# nothing yet\\n\\n") == []\n\n\ndef '
        'test_parse_strips_title_whitespace():\n    assert parse_document("episode:   '
        'Padded   \\n") == ["Padded"]\n```\n\nThe second one pins the strip, because the '
        "page's anchors are built from titles and a trailing space would make two "
        "anchors for one episode.",
    ),
    Turn(
        "user",
        "Feed ids: F1, F2, ... from a counter in `add_feed`. The page script uses them "
        "as anchors (`#F12`). A friend said ids should be a hash of the url so the same "
        "feed always gets the same id even if the store is rebuilt. That is tempting "
        "because the nightly script does rebuild the store from scratch. What do you "
        "think? Also, I hit the usual None problem in the page script when a feed was "
        "renumbered:\n\n```\nTraceback (most recent call last):\n  File "
        '"/volume1/scripts/page.py", line 22, in <module>\n    heading = store.find('
        "\"F61\").title\nAttributeError: 'NoneType' object has no attribute 'title'\n"
        "```",
    ),
    Turn(
        "assistant",
        "Stable anchors are a real need, but hashing the url is the wrong place to solve "
        "it: urls change (feeds move hosts), and a hash in an anchor is unreadable. Keep "
        "the counter and make the rebuild deterministic instead: add feeds from a "
        "subscriptions file in a fixed order, so F12 is always the twelfth line. If a "
        "feed is removed, leave its line as a comment so the numbers after it do not "
        "shift. For the None: `find` returns None because the name promises a search; "
        "methods that *act* on a feed (refreshing, archiving) raise KeyError on an "
        "unknown id, because acting on a feed that is not there is a bug in the "
        "caller. Your traceback becomes `KeyError: 'F61'` at the action, which names "
        "the actual problem. A `require` wrapper covers lookups that want to fail "
        "hard:\n\n```python\ndef require(store, feed_id):\n    feed = store.find(feed_id)\n"
        "    if feed is None:\n        raise KeyError(feed_id)\n    return feed\n```",
    ),
    Turn(
        "user",
        "Agreed: lookups return None, actions raise KeyError. Next, reading the mirrored "
        "files. I added `read_document(path)` in source.py, which is just "
        "`Path(path).read_text(encoding='utf-8')`. The fetcher writes files atomically "
        "(temp file then rename), so a half-written file should never be seen, but a "
        "missing file will happen when a feed is new and has not been fetched yet. Is "
        "it worth having `read_document` return an empty string for a missing file so "
        "the store treats it as a quiet feed? This is what the first night looked like "
        "for the two feeds I had just added:\n\n```\nTraceback (most recent call last):\n"
        '  File "/volume1/scripts/refresh.py", line 17, in <module>\n    text = '
        'read_document(path)\n  File "/volume1/scripts/podshelf/source.py", line 7, in '
        'read_document\n    return Path(path).read_text(encoding="utf-8")\n'
        "FileNotFoundError: [Errno 2] No such file or directory: "
        "'/volume1/mirror/F61.txt'\n```\n\nand the page for that night was simply not "
        "generated, which is the worst of both worlds.",
    ),
    Turn(
        "assistant",
        "No; a missing file and a quiet feed are different facts and the page should "
        "show them differently ('not fetched yet' versus 'no episodes'). Let "
        "`read_document` raise the OSError it gets from `read_text`; the refresh script "
        "already handles per-feed failures, so a new feed simply shows as 'not fetched "
        "yet' the first night. Returning an empty string would also mask a permissions "
        "problem on the NAS as a quiet feed forever. Keep `read_document` as the "
        "one-liner it is; its whole value is being the single place that knows the "
        "encoding. The per-feed loop in the refresh script then reads naturally:\n\n"
        '```python\nfor feed in store.all():\n    path = MIRROR / f"{feed.feed_id}.txt"\n'
        "    if not path.exists():\n        not_fetched.append(feed.feed_id)\n        "
        "continue\n    try:\n        refresh(store, feed.feed_id, path)\n    except Exception as "
        'exc:\n        failures.append((feed.feed_id, exc))\n        continue\nprint(f"'
        'refreshed {store.count() - len(failures)}, failed {len(failures)}")\n```\n\nwhere '
        "`refresh` is whatever the store grows next, and the `except` gets narrowed to "
        "the package's own exception once there is one to name. The `not_fetched` list "
        "feeds the 'not fetched yet' marker on the page, so the two facts stay distinct "
        "all the way to the reader.",
    ),
    Turn(
        "user",
        "Two conventions to fix before the store grows. First, the error surface: "
        "anything that fails underneath a public FeedStore method, a document that does "
        "not parse, a file that cannot be read, gets wrapped in PodshelfError (already "
        "in model.py). The page script catches one exception type per feed and moves "
        "on. Chain the original with `from exc` so the cause is kept.",
    ),
    Turn(
        "assistant",
        "Understood: public FeedStore methods wrap lower-layer failures (parsing, file "
        "I/O) in PodshelfError with `raise PodshelfError(...) from exc`, so the script "
        "catches one type and the original is on `__cause__`. KeyError for an unknown "
        "feed id is the store's own contract, not a lower-layer failure, so it stays a "
        "plain KeyError.",
    ),
    Turn(
        "user",
        "Second, naming: public FeedStore methods are verb_noun, like add_feed. New "
        "methods follow that pattern so the class reads as a list of actions.",
    ),
    Turn(
        "assistant",
        "Noted: verb_noun for new public FeedStore methods, matching add_feed. Private "
        "helpers can be named freely. Where the verb is ambiguous I will use the verb the "
        "request itself uses.",
    ),
    Turn(
        "user",
        "For later: the page needs 'newest first' across all feeds, which needs dates "
        "the document does not carry yet. I will extend the format to `episode: "
        "2026-09-11 | Title` at some point; when that happens the parser changes and "
        "Feed grows an `episodes` of records rather than titles. Not now.",
    ),
    Turn(
        "assistant",
        "Noted. When the format grows a date, keep `parse_document` returning plain "
        "records and let the old title-only form parse too for a release or two, so the "
        "fetcher and podshelf do not have to change on the same night.",
    ),
    Turn(
        "user",
        "The tests that exist today are only these; I will paste the current files with "
        "each request so you see the real state:\n\n```python\nfrom podshelf.store "
        "import FeedStore\n\n\ndef test_add_feed_mints_sequential_ids():\n    s = "
        'FeedStore()\n    assert s.add_feed("Weekly", "u").feed_id == "F1"\n    assert '
        's.add_feed("Daily", "v").feed_id == "F2"\n\n\ndef test_find_missing_is_none():\n'
        '    assert FeedStore().find("F1") is None\n\n\ndef test_new_feed_has_no_episodes'
        '():\n    assert FeedStore().add_feed("Weekly", "u").episodes == ()\n```',
    ),
    Turn(
        "assistant",
        "Good. Send the first request and I will return the complete store module, "
        "keeping add_feed, find and count exactly as they are.",
    ),
]

_EVENT = (
    "Change of convention, effective now: new public FeedStore methods are named "
    "noun_verb (feed_archive style), not verb_noun. Existing method names stay as they "
    "are, including anything already added; only new methods follow the new pattern."
)


def build() -> Session:
    return Session(
        id="S10",
        project="podshelf",
        target_family="naming",
        support_family="error_surface",
        lifecycle="replacement",
        files=_FILES,
        prefix=_PREFIX,
        states=("verb_noun", "noun_verb"),
        state_at=("verb_noun", "noun_verb"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10),
    )
