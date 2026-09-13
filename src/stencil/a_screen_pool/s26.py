# ruff: noqa: E501
"""S26: translation glossary — validation (target, replacement) x error_surface=wrap (support)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '"""termbook package."""\n'

_MODEL = '''"""Glossary term records."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Term:
    source: str
    target: str
    lang: str
    note: str = ""
'''

_ERRORS = '''"""Package exceptions."""


class TermbookError(Exception):
    """Raised when the glossary file cannot be written or read."""
'''


def _book(store_extra: str = "", api_extra: str = "", use_replace: bool = False) -> str:
    imports = (
        "from dataclasses import asdict, replace"
        if use_replace
        else "from dataclasses import asdict"
    )
    return f'''"""Glossary store and public operations."""

import json
{imports}
from pathlib import Path

from termbook.errors import TermbookError
from termbook.model import Term


class TermBook:
    def __init__(self, path: Path) -> None:
        self._path = Path(path)
        self._terms: dict[str, Term] = {{}}

    def put(self, term: Term) -> Term:
        self._terms[term.source] = term
        self._save()
        return term

    def get(self, source: str) -> Term | None:
        return self._terms.get(source)
{store_extra}
    def _save(self) -> None:
        rows = [asdict(t) for t in self._terms.values()]
        try:
            self._path.write_text(json.dumps(rows, ensure_ascii=False, indent=1))
        except OSError as exc:
            raise TermbookError(f"cannot write {{self._path}}") from exc


def add_term(book: TermBook, source: str, target: str, lang: str) -> Term:
    if not source.strip() or not target.strip():
        raise ValueError("source and target must be non-empty")
    if len(lang) != 2:
        raise ValueError("lang must be a two-letter code")
    return book.put(Term(source=source, target=target, lang=lang))
{api_extra}'''


_FILES = {
    "termbook/__init__.py": _INIT,
    "termbook/model.py": _MODEL,
    "termbook/errors.py": _ERRORS,
    "termbook/book.py": _book(),
}

# ----------------------------------------------------------------- checkpoint 1: set_note

_CHECK_NOTE = """        if not note.strip():
            raise ValueError("note must be non-empty")
"""


def _store_note(validate: bool) -> str:
    return (
        """
    def put_note(self, source: str, note: str) -> Term:
"""
        + (_CHECK_NOTE if validate else "")
        + """        updated = replace(self._terms[source], note=note)
        self._terms[source] = updated
        self._save()
        return updated
"""
    )


def _api_note(validate: bool) -> str:
    return (
        """

def set_note(book: TermBook, source: str, note: str) -> Term:
"""
        + (
            '    if not note.strip():\n        raise ValueError("note must be non-empty")\n'
            if validate
            else ""
        )
        + "    return book.put_note(source, note)\n"
    )


def _gold1(state: str) -> str:
    api = state == "api"
    return _book(_store_note(not api), _api_note(api), use_replace=True)


_C1_SETUP = """import pytest

from termbook.book import TermBook, add_term, set_note
from termbook.model import Term


def _book(tmp_path):
    book = TermBook(tmp_path / "terms.json")
    add_term(book, "cat", "gato", "es")
    add_term(book, "dog", "perro", "es")
    return book
"""

_C1_FUNCTIONAL = {
    "test_note_functional.py": _C1_SETUP
    + """

def test_set_note_stores_and_returns_updated_term(tmp_path):
    book = _book(tmp_path)
    out = set_note(book, "cat", "feline; not the verb")
    assert isinstance(out, Term)
    assert out.note == "feline; not the verb"
    assert out.target == "gato" and out.lang == "es"
    assert book.get("cat").note == "feline; not the verb"


def test_set_note_persists_to_file(tmp_path):
    book = _book(tmp_path)
    set_note(book, "dog", "domestic only")
    assert '"domestic only"' in (tmp_path / "terms.json").read_text()


def test_set_note_rejects_blank_note(tmp_path):
    book = _book(tmp_path)
    with pytest.raises(ValueError):
        set_note(book, "cat", "   ")
    assert book.get("cat").note == ""


def test_set_note_unknown_source_raises_keyerror(tmp_path):
    book = _book(tmp_path)
    with pytest.raises(KeyError):
        set_note(book, "horse", "equine")


def _saved_sources(tmp_path):
    import json

    rows = json.loads((tmp_path / "terms.json").read_text())
    return sorted(r["source"] for r in rows)


def test_set_note_keeps_the_other_term_and_the_row_count(tmp_path):
    book = _book(tmp_path)
    kept = set_note(book, "dog", "canine; the animal")
    out = set_note(book, "cat", "feline; not the verb")
    assert out.note == "feline; not the verb" and out.target == "gato"
    assert book.get("cat").note == "feline; not the verb"
    back = book.get("dog")
    assert back is not None, "noting one term dropped the other"
    assert back == kept and back.note == "canine; the animal"
    assert back.target == "perro" and back.lang == "es"
    assert _saved_sources(tmp_path) == ["cat", "dog"]


def test_set_note_over_an_existing_note_keeps_the_rest(tmp_path):
    book = _book(tmp_path)
    set_note(book, "dog", "canine; the animal")
    set_note(book, "cat", "first reading")
    out = set_note(book, "cat", "second reading")
    assert out.note == "second reading" and out.source == "cat"
    assert out.target == "gato" and out.lang == "es"
    stored = book.get("cat")
    assert stored.note == "second reading" and stored.target == "gato"
    back = book.get("dog")
    assert back is not None, "noting one term dropped the other"
    assert back.note == "canine; the animal" and back.target == "perro"
    assert _saved_sources(tmp_path) == ["cat", "dog"]
"""
}

_C1_REGRESSION = {
    "test_note_regression.py": """import json

import pytest

from termbook.book import TermBook, add_term


def test_add_term_and_get_unchanged(tmp_path):
    book = TermBook(tmp_path / "terms.json")
    t = add_term(book, "cat", "gato", "es")
    assert book.get("cat") is t and t.note == ""
    assert book.get("nope") is None
    rows = json.loads((tmp_path / "terms.json").read_text())
    assert rows == [{"source": "cat", "target": "gato", "lang": "es", "note": ""}]


def test_add_term_still_validates_in_public_function(tmp_path):
    book = TermBook(tmp_path / "terms.json")
    with pytest.raises(ValueError):
        add_term(book, "", "gato", "es")
    with pytest.raises(ValueError):
        add_term(book, "cat", "gato", "spa")


def test_add_term_keeps_every_earlier_term(tmp_path):
    book = TermBook(tmp_path / "terms.json")
    first = add_term(book, "cat", "gato", "es")
    second = add_term(book, "dog", "perro", "es")
    assert book.get("cat") is first and book.get("dog") is second
    rows = json.loads((tmp_path / "terms.json").read_text())
    assert [r["source"] for r in rows] == ["cat", "dog"]
"""
}

_C1_CONTRACT = {
    "api": {
        "test_note_validation.py": _C1_SETUP
        + """

def test_public_set_note_raises_on_blank(tmp_path):
    book = _book(tmp_path)
    with pytest.raises(ValueError):
        set_note(book, "cat", "")


def test_store_put_note_trusts_its_argument(tmp_path):
    book = _book(tmp_path)
    out = book.put_note("cat", "")
    assert out.note == ""
    assert book.get("cat").note == ""
"""
    },
    "storage": {
        "test_note_validation.py": _C1_SETUP
        + """

def test_store_put_note_raises_on_blank(tmp_path):
    book = _book(tmp_path)
    with pytest.raises(ValueError):
        book.put_note("cat", "")
    assert book.get("cat").note == ""


def test_public_set_note_delegates_without_precheck(tmp_path, monkeypatch):
    book = _book(tmp_path)
    calls = []

    def spy(self, *args, **kwargs):
        calls.append(args + tuple(kwargs.values()))
        return self._terms["cat"]

    monkeypatch.setattr(TermBook, "put_note", spy)
    set_note(book, "cat", "")
    assert len(calls) == 1 and "" in calls[0]
"""
    },
}

_C1_SUPPORT = {
    "test_note_errors.py": """import shutil

import pytest

from termbook.book import TermBook, add_term, set_note
from termbook.errors import TermbookError


def test_set_note_wraps_write_failure(tmp_path):
    folder = tmp_path / "glossary"
    folder.mkdir()
    book = TermBook(folder / "terms.json")
    add_term(book, "cat", "gato", "es")
    shutil.rmtree(folder)
    with pytest.raises(TermbookError) as info:
        set_note(book, "cat", "feline")
    assert not isinstance(info.value, OSError)


def test_set_note_no_error_on_healthy_file(tmp_path):
    book = TermBook(tmp_path / "terms.json")
    add_term(book, "cat", "gato", "es")
    assert set_note(book, "cat", "feline").note == "feline"
"""
}

_REQ1 = Request(
    text=(
        "Add a note operation. Public function `set_note(book, source, note)` in "
        "termbook/book.py stores a translator note on an existing term and returns the "
        "updated Term; the store side is a new method `TermBook.put_note(source, note)` "
        "that swaps in the updated record and saves. A blank note (empty or whitespace "
        "only) is invalid and is rejected with ValueError; an unknown source raises "
        "KeyError."
    ),
    target="termbook/book.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold={"api": _gold1("api"), "storage": _gold1("storage")},
)

# ----------------------------------------------------------------- checkpoint 2: rename_target


def _store_target(validate: bool) -> str:
    return (
        """
    def put_target(self, source: str, target: str) -> Term:
"""
        + (
            '        if not target.strip():\n            raise ValueError("target must be non-empty")\n'
            if validate
            else ""
        )
        + """        updated = replace(self._terms[source], target=target)
        self._terms[source] = updated
        self._save()
        return updated
"""
    )


def _api_target(validate: bool) -> str:
    return (
        """

def rename_target(book: TermBook, source: str, target: str) -> Term:
"""
        + (
            '    if not target.strip():\n        raise ValueError("target must be non-empty")\n'
            if validate
            else ""
        )
        + "    return book.put_target(source, target)\n"
    )


def _gold2(state: str) -> str:
    # Built on the checkpoint-1 gold under the state then in force (api).
    api = state == "api"
    return _book(
        _store_note(False) + _store_target(not api),
        _api_note(True) + _api_target(api),
        use_replace=True,
    )


_C2_SETUP = """import pytest

from termbook.book import TermBook, add_term, rename_target, set_note
from termbook.model import Term


def _book(tmp_path):
    book = TermBook(tmp_path / "terms.json")
    add_term(book, "cat", "gato", "es")
    set_note(book, "cat", "feline")
    add_term(book, "dog", "perro", "es")
    return book
"""

_C2_FUNCTIONAL = {
    "test_target_functional.py": _C2_SETUP
    + """

def test_rename_target_updates_and_returns_term(tmp_path):
    book = _book(tmp_path)
    out = rename_target(book, "cat", "gata")
    assert isinstance(out, Term)
    assert out.target == "gata" and out.source == "cat"
    assert out.note == "feline" and out.lang == "es"
    assert book.get("cat").target == "gata"


def test_rename_target_persists(tmp_path):
    book = _book(tmp_path)
    rename_target(book, "dog", "perra")
    assert '"perra"' in (tmp_path / "terms.json").read_text()


def test_rename_target_rejects_blank(tmp_path):
    book = _book(tmp_path)
    with pytest.raises(ValueError):
        rename_target(book, "cat", " ")
    assert book.get("cat").target == "gato"


def test_rename_target_unknown_source_raises_keyerror(tmp_path):
    book = _book(tmp_path)
    with pytest.raises(KeyError):
        rename_target(book, "horse", "caballo")


def _saved_sources(tmp_path):
    import json

    rows = json.loads((tmp_path / "terms.json").read_text())
    return sorted(r["source"] for r in rows)


def test_rename_target_keeps_the_other_term_and_the_note(tmp_path):
    book = _book(tmp_path)
    kept = set_note(book, "dog", "canine; the animal")
    out = rename_target(book, "cat", "gata")
    assert out.target == "gata" and out.note == "feline"
    assert out.lang == "es" and out.source == "cat"
    stored = book.get("cat")
    assert stored.target == "gata" and stored.note == "feline"
    assert stored.lang == "es"
    back = book.get("dog")
    assert back is not None, "renaming one target dropped the other term"
    assert back == kept and back.target == "perro"
    assert back.note == "canine; the animal" and back.lang == "es"
    assert _saved_sources(tmp_path) == ["cat", "dog"]


def test_rename_target_twice_keeps_note_and_other_term(tmp_path):
    book = _book(tmp_path)
    set_note(book, "dog", "canine; the animal")
    rename_target(book, "cat", "gata")
    out = rename_target(book, "cat", "minina")
    assert out.target == "minina" and out.note == "feline"
    assert book.get("cat").note == "feline"
    back = book.get("dog")
    assert back is not None, "renaming one target dropped the other term"
    assert back.note == "canine; the animal" and back.target == "perro"
    assert _saved_sources(tmp_path) == ["cat", "dog"]
"""
}

_C2_REGRESSION = {
    "test_target_regression.py": """import json

import pytest

from termbook.book import TermBook, add_term, set_note


def test_add_term_get_and_set_note_unchanged(tmp_path):
    book = TermBook(tmp_path / "terms.json")
    t = add_term(book, "cat", "gato", "es")
    assert book.get("cat") is t
    assert set_note(book, "cat", "feline").note == "feline"
    with pytest.raises(ValueError):
        set_note(book, "cat", "")
    with pytest.raises(ValueError):
        add_term(book, "", "gato", "es")


def test_set_note_keeps_the_other_term(tmp_path):
    book = TermBook(tmp_path / "terms.json")
    add_term(book, "cat", "gato", "es")
    add_term(book, "dog", "perro", "es")
    kept = set_note(book, "dog", "canine; the animal")
    out = set_note(book, "cat", "feline")
    assert out.note == "feline" and out.target == "gato"
    assert book.get("cat").note == "feline"
    back = book.get("dog")
    assert back is not None, "noting one term dropped the other"
    assert back == kept and back.note == "canine; the animal"
    assert back.target == "perro" and back.lang == "es"
    rows = json.loads((tmp_path / "terms.json").read_text())
    assert sorted(r["source"] for r in rows) == ["cat", "dog"]
"""
}

_C2_CONTRACT = {
    "api": {
        "test_target_validation.py": _C2_SETUP
        + """

def test_public_rename_target_raises_on_blank(tmp_path):
    book = _book(tmp_path)
    with pytest.raises(ValueError):
        rename_target(book, "cat", "")


def test_store_put_target_trusts_its_argument(tmp_path):
    book = _book(tmp_path)
    out = book.put_target("cat", "")
    assert out.target == ""
    assert book.get("cat").target == ""
"""
    },
    "storage": {
        "test_target_validation.py": _C2_SETUP
        + """

def test_store_put_target_raises_on_blank(tmp_path):
    book = _book(tmp_path)
    with pytest.raises(ValueError):
        book.put_target("cat", "")
    assert book.get("cat").target == "gato"


def test_public_rename_target_delegates_without_precheck(tmp_path, monkeypatch):
    book = _book(tmp_path)
    calls = []

    def spy(self, *args, **kwargs):
        calls.append(args + tuple(kwargs.values()))
        return self._terms["cat"]

    monkeypatch.setattr(TermBook, "put_target", spy)
    rename_target(book, "cat", "")
    assert len(calls) == 1 and "" in calls[0]
"""
    },
}

_C2_SUPPORT = {
    "test_target_errors.py": """import shutil

import pytest

from termbook.book import TermBook, add_term, rename_target
from termbook.errors import TermbookError


def test_rename_target_wraps_write_failure(tmp_path):
    folder = tmp_path / "glossary"
    folder.mkdir()
    book = TermBook(folder / "terms.json")
    add_term(book, "cat", "gato", "es")
    shutil.rmtree(folder)
    with pytest.raises(TermbookError) as info:
        rename_target(book, "cat", "gata")
    assert not isinstance(info.value, OSError)


def test_rename_target_no_error_on_healthy_file(tmp_path):
    book = TermBook(tmp_path / "terms.json")
    add_term(book, "cat", "gato", "es")
    assert rename_target(book, "cat", "gata").target == "gata"
"""
}

_REQ2 = Request(
    text=(
        "Add a rename operation for the target side. Public function "
        "`rename_target(book, source, target)` in termbook/book.py replaces the target "
        "text of an existing term and returns the updated Term; the store side is a new "
        "method `TermBook.put_target(source, target)` that swaps in the updated record "
        "and saves. A blank target (empty or whitespace only) is invalid and is rejected "
        "with ValueError; an unknown source raises KeyError."
    ),
    target="termbook/book.py",
    functional_tests=_C2_FUNCTIONAL,
    regression_tests=_C2_REGRESSION,
    contract_tests=_C2_CONTRACT,
    support_tests=_C2_SUPPORT,
    gold={"api": _gold2("api"), "storage": _gold2("storage")},
)

# ----------------------------------------------------------------- prefix (16 turns)

_PREFIX = [
    Turn(
        "user",
        "I run localisation for a four-person translation team and we keep our product "
        "glossary in a shared spreadsheet that nobody trusts any more. I want a tiny Python "
        "package, `termbook`, that holds the glossary as a JSON file and gives the "
        "translators a couple of scripts: add a term, look one up, dump the whole thing "
        "for the CAT tool. No web service, no database. The JSON I have in mind is flat:\n\n"
        '```json\n[\n  {"source": "checkout", "target": "caja", "lang": "es", '
        '"note": "the page, not the verb"},\n  {"source": "cart", "target": '
        '"carrito", "lang": "es", "note": ""}\n]\n```\n\nSource strings are unique '
        "per file because we keep one file per target language. Can you draft the README "
        "scope section so the team knows what this is and is not? They have asked for "
        "termbase import, TBX export and machine-translation hooks before and I want to say "
        "no politely and in writing.",
    ),
    Turn(
        "assistant",
        "Something like this keeps it honest:\n\n```\n## Scope\ntermbook is a single-file "
        "glossary for one target language. A TermBook loads and saves a JSON list of Term "
        "records (source, target, lang, note) and exposes a handful of functions that "
        "scripts call. It has no server, no concurrency story and no format other than "
        "its own JSON.\n\n## Non-goals\n- TBX or TMX import/export\n- machine-translation "
        "hooks\n- multi-language files (use one TermBook per language)\n```\n\nThe usage "
        "block can be three lines:\n\n```python\nfrom termbook.book import TermBook, "
        'add_term\n\nbook = TermBook("glossary-es.json")\nadd_term(book, "checkout", '
        '"caja", "es")\nprint(book.get("checkout"))\n```\n\nIf anyone wants TBX later, '
        "a converter script can read the JSON; nothing in the package needs to know.",
    ),
    Turn(
        "user",
        "Keying on the source string rather than a numeric id: any regret waiting for me? "
        'The translators think in source strings, so `book.get("checkout")` is what they '
        "would type, but I have been bitten by natural keys before. The cases I can think "
        'of are case ("Checkout" vs "checkout"), trailing spaces from copy-paste, and '
        "the same source word needing two targets depending on context, which we currently "
        "handle in the spreadsheet with a second row and a note. Today the reviewer "
        'script does roughly:\n\n```python\nfor row in rows:\n    if row["source"].lower() '
        'in seen:\n        print("dup:", row["source"])\n    seen.add(row["source"]'
        ".lower())\n```\n\nwhich is exactly the kind of thing I would like the package to make "
        "unnecessary. The spreadsheet currently has 412 rows for Spanish, 380 for German and "
        "a half-finished 90 for Portuguese, so the files stay small whatever we decide.",
    ),
    Turn(
        "assistant",
        "Natural keys are fine here because the source string is the identity the "
        "translators actually use; a numeric id would just be a second thing to look up. "
        "The three cases you list are real but small. Case and whitespace are a "
        "normalisation question: decide once that the key is the source text exactly as "
        "given, and have the add script strip whitespace before calling in. The two-targets "
        "case is the only one that argues for a richer key, and the note field already "
        "covers it the way the spreadsheet does. If it grows, the key can become "
        "`(source, context)` later without touching callers of `get`, since `get` would "
        "accept an optional context and default it. I would not pre-build that. The "
        "duplicate scan you pasted becomes unnecessary because `put` overwrites by source, "
        "so a file can never hold two rows with the same key. If you want the case "
        "question closed too, a one-line check in the add script is enough:\n\n```python\n"
        'if source != source.strip():\n    sys.exit(f"source has surrounding whitespace: '
        '{source!r}")\n```\n\nThat keeps the package itself free of policy about what '
        "counts as the same word.",
    ),
    Turn(
        "user",
        "Persistence: I want every change written straight to the JSON file, no explicit "
        "save call, because the translators will use the scripts one command at a time and "
        "will forget to save. That means every store method ends with a write. I drafted "
        "the test I want for that so you can see the behaviour I mean:\n\n```python\nimport "
        "json\n\nfrom termbook.book import TermBook, add_term\n\n\ndef test_add_writes_"
        'immediately(tmp_path):\n    path = tmp_path / "terms.json"\n    book = TermBook('
        'path)\n    add_term(book, "cart", "carrito", "es")\n    rows = json.loads('
        'path.read_text())\n    assert rows == [{"source": "cart", "target": '
        '"carrito", "lang": "es", "note": ""}]\n```\n\nIs a full rewrite of the '
        "file on every change acceptable, or should I be appending?",
    ),
    Turn(
        "assistant",
        "Full rewrite is the right call. The file is a few hundred rows at most, the "
        "rewrite is milliseconds, and it keeps the on-disk format a plain JSON list that "
        "any tool can read. Appending would force a line-delimited format and a compaction "
        "step, and the moment two rows share a source you are back to the duplicate scan. "
        "Keep a single private `_save` on the store that serialises `self._terms.values()` "
        "with `indent=1` and `ensure_ascii=False` so accented targets stay readable in "
        "diffs, and have every mutating method call it last. Your test is exactly right; I "
        "would add one that overwrites an existing source and checks the file still has one "
        "row for it:\n\n```python\ndef test_put_overwrites_by_source(tmp_path):\n    path = "
        'tmp_path / "terms.json"\n    book = TermBook(path)\n    add_term(book, "cart", '
        '"carrito", "es")\n    add_term(book, "cart", "cesta", "es")\n    rows = json.loads('
        'path.read_text())\n    assert len(rows) == 1 and rows[0]["target"] == "cesta"\n'
        "```",
    ),
    Turn(
        "user",
        "Here is what happened when Marta ran the add script from a folder that had been "
        "moved by IT. I want to talk about how the package should present this kind of "
        "failure before we write more of it:\n\n```\n$ python -m termbook.add checkout caja "
        'es\nTraceback (most recent call last):\n  File "/home/marta/glossary/termbook/'
        'add.py", line 14, in <module>\n    main()\n  File "/home/marta/glossary/termbook/'
        'add.py", line 11, in main\n    add_term(book, args.source, args.target, args.lang)'
        '\n  File "/home/marta/glossary/termbook/book.py", line 19, in put\n    self._save()'
        '\n  File "/home/marta/glossary/termbook/book.py", line 27, in _save\n    self._path'
        ".write_text(json.dumps(rows))\nFileNotFoundError: [Errno 2] No such file or "
        "directory: '/mnt/loc/es/glossary-es.json'\n```\n\nShe read that as the term being "
        "missing, not the folder, and re-typed it three times.",
    ),
    Turn(
        "assistant",
        "That traceback is honest but it speaks the file system's language, not the "
        "glossary's. The fix is one layer of translation at the boundary where the package "
        "touches disk: `_save` catches `OSError`, raises a package exception with the path "
        "in the message, and chains the original with `from exc` so the errno is still "
        "there for whoever debugs it. The scripts then catch the package exception and "
        "print one line. A `TermbookError` class in `termbook/errors.py` is enough; you do "
        "not need a hierarchy until there is a second kind of failure worth distinguishing. "
        "The message Marta needed was roughly `cannot write /mnt/loc/es/glossary-es.json`, "
        "which is what the wrapper produces. In the script it reads:\n\n```python\ntry:\n"
        "    add_term(book, args.source, args.target, args.lang)\nexcept TermbookError as "
        'exc:\n    sys.exit(f"termbook: {exc}")\n```\n\nand the full chained traceback is '
        "still one `--verbose` flag away if IT wants to see the errno.",
    ),
    Turn(
        "user",
        "Agreed, and let's make that a rule rather than a one-off: anything that fails "
        "while reading or writing the glossary file surfaces to callers as TermbookError, "
        "chained from the original. No raw OSError or JSONDecodeError escapes a public "
        "operation. Every operation that touches the file goes through that wrapping.",
    ),
    Turn(
        "assistant",
        "Noted: file-level failures are always wrapped in TermbookError with the original "
        "chained as the cause, and no public operation lets a raw OSError or "
        "JSONDecodeError escape. Since every mutating method ends in `_save`, the wrapper "
        "there covers them all; a future `load` would wrap its read and parse the same way, "
        "so a corrupt file reads as `cannot read <path>` rather than a JSON position error.",
    ),
    Turn(
        "user",
        "Now the other rule, input checking. I want validation to live in the public "
        "functions in book.py, the ones scripts call: `add_term` and whatever comes next "
        "raise ValueError on bad input, and TermBook itself stays a dumb store that trusts "
        "its arguments and never checks them. Same for any new operation we add.",
    ),
    Turn(
        "assistant",
        "Understood: validation belongs to the public functions, which raise ValueError on "
        "bad input, and TermBook methods trust what they are given and do no checking. New "
        "operations follow the same split, so a store method called directly with a bad "
        "value simply stores it.",
    ),
    Turn(
        "user",
        "The tests we have so far, for reference, all against the public functions:\n\n"
        "```python\ndef test_add_rejects_empty_source(tmp_path):\n    book = TermBook("
        'tmp_path / "t.json")\n    with pytest.raises(ValueError):\n        add_term(book, '
        '"", "caja", "es")\n\n\ndef test_add_rejects_long_lang(tmp_path):\n    book = '
        'TermBook(tmp_path / "t.json")\n    with pytest.raises(ValueError):\n        '
        'add_term(book, "checkout", "caja", "spa")\n```\n\nBoth pass against the current '
        "book module; they run in about 40 ms on Marta's laptop.",
    ),
    Turn(
        "assistant",
        "Those match the split. If you want a third, `test_get_missing_returns_none` pins "
        "the lookup contract: `get` returns None for an unknown source rather than raising, "
        "which the scripts rely on when they print 'not in glossary'. Actions on a term "
        "that does not exist are a different matter and should raise KeyError, since a "
        "script asking to change a missing term has a bug, not a question.",
    ),
    Turn(
        "user",
        "Good. Next up is the note field: reviewers want to attach a short context note to "
        "an existing term without retyping it, and after that a way to fix a target "
        "without losing the note. I will paste the current files with each request so you "
        "see the real state, not my memory of it.",
    ),
    Turn(
        "assistant",
        "Ready. Send the request with the files and I will return the complete book "
        "module, keeping `add_term`, `put` and `get` exactly as they are.",
    ),
]

_EVENT = (
    "Change of convention, effective now: input validation moves down into TermBook. New "
    "store methods raise ValueError on bad input themselves, and the public functions in "
    "book.py just call through and let that propagate, with no separate pre-check of their "
    "own. Existing functions keep their checks where they are; only new operations follow "
    "the new split. The reason is that the bulk importer we are adding calls the store "
    "directly, so checks that live only in the public functions would be bypassed."
)


def build() -> Session:
    return Session(
        id="S26",
        project="termbook",
        target_family="validation",
        support_family="error_surface",
        lifecycle="replacement",
        files=_FILES,
        prefix=_PREFIX,
        states=("api", "storage"),
        state_at=("api", "storage"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10),
    )
