# ruff: noqa: E501
"""S01: recipes — naming (target, stable) x return_shape (support)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '"""recipebook package."""\n'

_MODEL = '''"""Recipe records."""

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Recipe:
    recipe_id: str
    title: str
    servings: int = 4
    tags: tuple[str, ...] = ()

    def with_servings(self, servings: int) -> "Recipe":
        return replace(self, servings=servings)
'''

_BOOK = '''"""In-memory recipe book."""

from recipebook.model import Recipe


class RecipeBook:
    def __init__(self) -> None:
        self._recipes: dict[str, Recipe] = {}
        self._counter = 0

    def add_recipe(self, title: str, servings: int = 4) -> Recipe:
        self._counter += 1
        recipe = Recipe(recipe_id=f"R{self._counter}", title=title, servings=servings)
        self._recipes[recipe.recipe_id] = recipe
        return recipe

    def find(self, recipe_id: str) -> Recipe | None:
        return self._recipes.get(recipe_id)

    def count(self) -> int:
        return len(self._recipes)
'''

_FILES = {
    "recipebook/__init__.py": _INIT,
    "recipebook/model.py": _MODEL,
    "recipebook/book.py": _BOOK,
}

# ----------------------------------------------------------------- checkpoint 1: scale

_C1_HELPER = """from recipebook.book import RecipeBook
from recipebook.model import Recipe


def _scale(book):
    fn = getattr(book, "scale_recipe", None) or getattr(book, "recipe_scale", None)
    assert fn is not None, "no scale method found"
    return fn
"""

_C1_FUNCTIONAL = {
    "test_scale_functional.py": _C1_HELPER
    + """

def test_scale_sets_servings():
    b = RecipeBook()
    r = b.add_recipe("lentil soup", servings=4)
    out = _scale(b)(r.recipe_id, 10)
    assert out.servings == 10
    assert b.find(r.recipe_id).servings == 10


def test_scale_keeps_title_id_and_tags():
    b = RecipeBook()
    r = b.add_recipe("flatbread", servings=2)
    out = _scale(b)(r.recipe_id, 6)
    assert out.recipe_id == r.recipe_id and out.title == "flatbread"
    assert out.tags == ()


def test_scale_unknown_raises_keyerror():
    b = RecipeBook()
    try:
        _scale(b)("R404", 3)
    except KeyError:
        return
    raise AssertionError("expected KeyError for an unknown recipe")
"""
}

_C1_REGRESSION = {
    "test_scale_regression.py": """from recipebook.book import RecipeBook


def test_add_and_find_unchanged():
    b = RecipeBook()
    r = b.add_recipe("a")
    assert r.recipe_id == "R1" and r.servings == 4 and r.tags == ()
    assert b.find("R1") is r
    assert b.find("nope") is None
    assert b.count() == 1
"""
}

_C1_CONTRACT = {
    "verb_noun": {
        "test_scale_naming.py": """from recipebook.book import RecipeBook


def test_scale_is_verb_noun():
    assert hasattr(RecipeBook, "scale_recipe")
    assert not hasattr(RecipeBook, "recipe_scale")
"""
    },
    "noun_verb": {
        "test_scale_naming.py": """from recipebook.book import RecipeBook


def test_scale_is_noun_verb():
    assert hasattr(RecipeBook, "recipe_scale")
    assert not hasattr(RecipeBook, "scale_recipe")
"""
    },
}

_C1_SUPPORT = {
    "test_scale_shape.py": _C1_HELPER
    + """

def test_scale_returns_recipe_dataclass_not_dict():
    b = RecipeBook()
    r = b.add_recipe("x")
    out = _scale(b)(r.recipe_id, 8)
    assert isinstance(out, Recipe)
    assert not isinstance(out, dict)
"""
}


def _gold1(name: str) -> str:
    return (
        _BOOK.rstrip("\n")
        + f"""

    def {name}(self, recipe_id: str, servings: int) -> Recipe:
        recipe = self._recipes[recipe_id]
        scaled = recipe.with_servings(servings)
        self._recipes[recipe_id] = scaled
        return scaled
"""
    )


_REQ1 = Request(
    text=(
        "Add a public method on RecipeBook that scales a recipe by id to a new number of "
        "servings: it takes the recipe id and the servings count, stores the updated "
        "recipe and returns it. An unknown id raises KeyError."
    ),
    target="recipebook/book.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold={"verb_noun": _gold1("scale_recipe"), "noun_verb": _gold1("recipe_scale")},
)

# ----------------------------------------------------------------- checkpoint 2: tag

_C2_HELPER = """from recipebook.book import RecipeBook
from recipebook.model import Recipe


def _tag(book):
    fn = getattr(book, "tag_recipe", None) or getattr(book, "recipe_tag", None)
    assert fn is not None, "no tag method found"
    return fn
"""

_C2_FUNCTIONAL = {
    "test_tag_functional.py": _C2_HELPER
    + """

def test_tag_appends_tag():
    b = RecipeBook()
    r = b.add_recipe("lentil soup")
    out = _tag(b)(r.recipe_id, "vegan")
    assert out.tags == ("vegan",)
    assert b.find(r.recipe_id).tags == ("vegan",)


def test_tag_twice_keeps_order_and_no_duplicates():
    b = RecipeBook()
    r = b.add_recipe("flatbread")
    _tag(b)(r.recipe_id, "bread")
    _tag(b)(r.recipe_id, "quick")
    out = _tag(b)(r.recipe_id, "bread")
    assert out.tags == ("bread", "quick")
    assert out.title == "flatbread" and out.servings == 4


def test_tag_unknown_raises_keyerror():
    b = RecipeBook()
    try:
        _tag(b)("R404", "vegan")
    except KeyError:
        return
    raise AssertionError("expected KeyError for an unknown recipe")
"""
}

_C2_REGRESSION = {
    "test_tag_regression.py": """from recipebook.book import RecipeBook


def _scale(book):
    return getattr(book, "scale_recipe", None) or getattr(book, "recipe_scale", None)


def test_add_find_scale_unchanged():
    b = RecipeBook()
    r = b.add_recipe("a", servings=2)
    assert b.find("R1") is r and b.count() == 1
    assert _scale(b)(r.recipe_id, 5).servings == 5
"""
}

_C2_CONTRACT = {
    "verb_noun": {
        "test_tag_naming.py": """from recipebook.book import RecipeBook


def test_tag_is_verb_noun():
    assert hasattr(RecipeBook, "tag_recipe")
    assert not hasattr(RecipeBook, "recipe_tag")
"""
    },
    "noun_verb": {
        "test_tag_naming.py": """from recipebook.book import RecipeBook


def test_tag_is_noun_verb():
    assert hasattr(RecipeBook, "recipe_tag")
    assert not hasattr(RecipeBook, "tag_recipe")
"""
    },
}

_C2_SUPPORT = {
    "test_tag_shape.py": _C2_HELPER
    + """

def test_tag_returns_recipe_dataclass_not_dict():
    b = RecipeBook()
    r = b.add_recipe("x")
    out = _tag(b)(r.recipe_id, "quick")
    assert isinstance(out, Recipe)
    assert not isinstance(out, dict)
"""
}


def _gold2(name: str) -> str:
    # Built on the checkpoint-1 gold under the state then in force (verb_noun).
    body = (
        _gold1("scale_recipe").rstrip("\n")
        + f"""

    def {name}(self, recipe_id: str, tag: str) -> Recipe:
        recipe = self._recipes[recipe_id]
        if tag in recipe.tags:
            return recipe
        tagged = replace(recipe, tags=recipe.tags + (tag,))
        self._recipes[recipe_id] = tagged
        return tagged
"""
    )
    return body.replace(
        "from recipebook.model import Recipe\n",
        "from dataclasses import replace\n\nfrom recipebook.model import Recipe\n",
        1,
    )


_REQ2 = Request(
    text=(
        "Add a public method on RecipeBook that tags a recipe: it takes the recipe id and "
        "a tag string, appends the tag to the recipe's tags unless it is already present, "
        "stores the updated recipe and returns it. An unknown id raises KeyError."
    ),
    target="recipebook/book.py",
    functional_tests=_C2_FUNCTIONAL,
    regression_tests=_C2_REGRESSION,
    contract_tests=_C2_CONTRACT,
    support_tests=_C2_SUPPORT,
    gold={"verb_noun": _gold2("tag_recipe"), "noun_verb": _gold2("recipe_tag")},
)

# ----------------------------------------------------------------- prefix (16 turns)

_PREFIX = [
    Turn(
        "user",
        "I'm writing a small recipe package for the family cookbook. My mum has forty years "
        "of index cards, my sister typed most of them into a spreadsheet, and I want to turn "
        "that into something I can query from a script: an in-memory RecipeBook, a Recipe "
        "record, and eventually a `recipebook print R12` command that formats one card for "
        "the kitchen tablet. No database, no web app; a JSON dump of the book is the only "
        "persistence I'm planning. The spreadsheet columns are:\n\n```\ntitle, servings, "
        'tags, source, notes\nLentil soup, 6, "vegan;freezer", Mum, "double the cumin"\n'
        'Flatbread, 4, bread, Nan, "rest dough 20 min"\n```\n\nCan you sketch what the '
        "README should say about scope so my sister doesn't expect meal planning or a "
        "shopping list generator? She has already asked twice, and I'd rather write the "
        "non-goals down once than argue about them every Sunday.",
    ),
    Turn(
        "assistant",
        "A short scope section plus explicit non-goals works well:\n\n```\n## Scope\n"
        "recipebook is an in-memory recipe collection for a single process. It keeps Recipe "
        "records in a RecipeBook, has no persistence beyond an optional JSON dump and no "
        "concurrency guarantees, and is meant for scripts and tests rather than as a "
        "service.\n\n## Non-goals\n- meal planning\n- shopping lists\n- nutrition data\n- "
        "photos or attachments\n```\n\nThe non-goals list is what people actually read. A "
        "usage block sets the tone for the API:\n\n```python\nfrom recipebook.book import "
        'RecipeBook\n\nbook = RecipeBook()\nr = book.add_recipe("lentil soup", servings=6)\n'
        "print(book.find(r.recipe_id))\n```\n\nIf meal planning ever happens it can be a "
        "separate package that imports this one, which is a much easier conversation than "
        "carving it out later. One more README line worth having: `Requires Python 3.11+`, "
        "because the tablet image is older than your laptop and the first support question "
        "will otherwise be a syntax error on `str | None`.",
    ),
    Turn(
        "user",
        "Good. For ids I'm minting R1, R2, ... from a counter inside the book. My sister "
        "wants to use the spreadsheet row number instead so the ids match her sheet, and I "
        "can see the appeal, but rows get inserted and sorted and then the numbers drift. "
        "Is there a middle ground? The JSON dump I have in mind is nothing more than:\n\n"
        '```json\n{\n  "book": "family",\n  "exported_at": "2026-09-14T18:30:00",\n'
        '  "recipes": [\n    {"recipe_id": "R1", "title": "Lentil soup", "servings": 6, '
        '"tags": ["vegan", "freezer"]},\n    {"recipe_id": "R2", "title": "Flatbread", '
        '"servings": 4, "tags": ["bread"]}\n  ]\n}\n```\n\nand the importer would just '
        "call add_recipe per row in order, so the counter ids would line up with the sheet "
        "on the first import anyway. It is only later edits that would drift.",
    ),
    Turn(
        "assistant",
        "Keep the counter as the identity and carry the sheet row as data, not as the id. "
        "A counter is stable across sorts and inserts, easy to read in logs (`R14` beats a "
        "36-character uuid), and only `add_recipe` mints ids, so if persistence changes "
        "later there is one place to touch:\n\n```python\ndef _next_id(self) -> str:\n"
        '    self._counter += 1\n    return f"R{self._counter}"\n```\n\nIf your sister '
        "wants to find a recipe by its row, add an optional `source_row: int | None` field "
        "on Recipe and a lookup that scans for it. The first import will line up R-numbers "
        "with rows exactly as you say, and after that the row number becomes what it really "
        "is: provenance, not identity. Record it in the JSON dump so nothing is lost:\n\n"
        '```json\n{"recipe_id": "R1", "source_row": 2, "title": "Lentil soup"}\n```',
    ),
    Turn(
        "user",
        "I want a helper that formats a recipe as a one-line summary for the CLI, like "
        "`R3 lentil soup (serves 6) [vegan, freezer]`. Should it be a method on Recipe or a "
        "free function next to it? A method is discoverable, but then the record knows "
        "about presentation. Here is the test draft I have so far, so you can see the shape "
        "I am after:\n\n```python\nimport pytest\n\nfrom recipebook.model import Recipe\n\n\n"
        '@pytest.fixture\ndef soup():\n    return Recipe(recipe_id="R3", title="lentil soup", '
        "servings=6)\n\n\ndef test_summary_plain(soup):\n    assert summary(soup) == "
        '"R3 lentil soup (serves 6)"\n\n\ndef test_summary_with_tags():\n    r = Recipe('
        'recipe_id="R3", title="lentil soup", servings=6, tags=("vegan", "freezer"))\n'
        '    assert summary(r) == "R3 lentil soup (serves 6) [vegan, freezer]"\n```',
    ),
    Turn(
        "assistant",
        "Put it next to the model as a plain function so the CLI and tests share it without "
        "Recipe learning about presentation:\n\n```python\ndef summary(recipe: Recipe) -> "
        'str:\n    tags = f" [{", ".join(recipe.tags)}]" if recipe.tags else ""\n'
        '    return f"{recipe.recipe_id} {recipe.title} (serves {recipe.servings}){tags}"\n'
        "```\n\nIt reads only public fields, so it stays trivially testable, and if the "
        "tablet view later wants column alignment or colour that lives in the CLI module. A "
        "`__str__` on Recipe would tie the record to one rendering forever, and the JSON "
        "dump would still need its own serializer anyway. Your two tests pass against that "
        "function as written; I would add a third for the empty-title edge case, since the "
        "spreadsheet has at least one blank row that the importer will faithfully turn into "
        "a Recipe:\n\n```python\ndef test_summary_empty_title():\n    r = Recipe("
        'recipe_id="R7", title="", servings=1)\n    assert summary(r) == "R7  (serves 1)"\n```',
    ),
    Turn(
        "user",
        "We'll add that with the CLI. Another question: should `find` raise on a missing id "
        "or return None? Right now it returns None and the caller checks. I want one rule I "
        "can point my sister at instead of deciding per method. This is what a caller hits "
        'today when it assumes `find` raises:\n\n```\n>>> book.find("R9").servings\n'
        'Traceback (most recent call last):\n  File "<stdin>", line 1, in <module>\n'
        "AttributeError: 'NoneType' object has no attribute 'servings'\n```\n\nWhich is "
        "the usual None-propagation trap, and it took her twenty minutes to work out that "
        "the id was simply wrong rather than the book being broken. The importer log from "
        "that session, for colour:\n\n```\n2026-09-13 18:02:11 INFO  importer: read 41 rows "
        "from cookbook.csv\n2026-09-13 "
        "18:04:37 ERROR tablet: AttributeError: 'NoneType' object has no attribute "
        "'servings'\n```",
    ),
    Turn(
        "assistant",
        "Returning None from `find` is the usual lookup contract: the name says 'try to "
        "find', and callers branch on the result. Methods that *act* on a recipe (scaling, "
        "tagging, archiving) are different: acting on an id that does not exist is a caller "
        "bug, so raising KeyError there is the clearer signal and it surfaces in tests "
        "immediately. So the rule is: lookups return None, actions raise KeyError. Keep "
        "`find` as it is, and callers that need a hard failure can wrap it:\n\n```python\n"
        "def require(book, recipe_id):\n    recipe = book.find(recipe_id)\n    if recipe is "
        "None:\n        raise KeyError(recipe_id)\n    return recipe\n```\n\nThe traceback "
        "you pasted becomes a KeyError('R9') at the call site, which is the message your "
        "sister actually needed. The log line then reads `KeyError: 'R9'` instead of an "
        "AttributeError three frames away from the real mistake, and the importer can keep "
        "using `find` for its 'skip if already present' check without any exception "
        "handling at all.",
    ),
    Turn(
        "user",
        "Agreed, actions raise KeyError on unknown ids. Two conventions I want to fix now "
        "so the code stays uniform. First: public RecipeBook methods always return Recipe "
        "dataclass instances, never dicts or tuples, even for convenience (lookups may return None and count() stays an int). The spreadsheet "
        "importer I wrote last year returned dicts and every caller ended up with "
        "`.get('servings')` sprinkled around.",
    ),
    Turn(
        "assistant",
        "Noted: every public RecipeBook method returns Recipe instances (or None from "
        "lookups), never dicts or tuples. Callers stay on one type, we can add fields to "
        "Recipe without breaking them, and the summary helper works on anything the book "
        "hands back.",
    ),
    Turn(
        "user",
        "Second: method naming. Public book methods are named verb_noun, like add_recipe. "
        "Anything new follows that pattern so the API reads as a list of things you do to "
        "a recipe.",
    ),
    Turn(
        "assistant",
        "Understood: verb_noun for public RecipeBook methods, matching add_recipe. I will "
        "name new methods that way; private helpers can stay free-form since they are not "
        "part of the API. If a verb is ambiguous, for example whether resizing a recipe is "
        "scale_recipe or resize_recipe, I will use the verb the request itself uses.",
    ),
    Turn(
        "user",
        "One more for later: I'd like `count` to eventually take an optional tag filter so "
        "the CLI can print how many freezer recipes we have. Not now. For reference, the "
        "tests that exist today are only these:\n\n```python\nfrom recipebook.book import "
        "RecipeBook\n\n\ndef test_add_assigns_sequential_ids():\n    b = RecipeBook()\n"
        '    assert b.add_recipe("a").recipe_id == "R1"\n    assert b.add_recipe("b").'
        'recipe_id == "R2"\n\n\ndef test_find_missing_returns_none():\n    assert '
        'RecipeBook().find("R1") is None\n\n\ndef test_count_after_two_adds():\n'
        '    b = RecipeBook()\n    b.add_recipe("a")\n    b.add_recipe("b")\n    assert '
        "b.count() == 2\n```",
    ),
    Turn(
        "assistant",
        "Noted for later. An optional keyword `tag: str | None = None` keeps the current "
        "no-argument call working, and the filter is a one-line comprehension:\n\n"
        "```python\ndef count(self, tag: str | None = None) -> int:\n    if tag is None:\n"
        "        return len(self._recipes)\n    return sum(1 for r in self._recipes.values() "
        "if tag in r.tags)\n```",
    ),
    Turn(
        "user",
        "Right. Let's get the first real feature in; Sunday lunch is for twelve this week "
        "and I want scaling to work before then. I will paste the current files with each "
        "request so you always see the real state rather than my memory of it.",
    ),
    Turn(
        "assistant",
        "Ready when you are. Send the request and I will return the full book module.",
    ),
]

_EVENT = (
    "Small housekeeping note before the next one: I moved the repo to a new GitHub org "
    "(family-kitchen/recipebook) and pointed CI at it. Nothing in the package changes; "
    "the badge in the README just needs updating at some point."
)


def build() -> Session:
    return Session(
        id="S01",
        project="recipebook",
        target_family="naming",
        support_family="return_shape",
        lifecycle="stable",
        files=_FILES,
        prefix=_PREFIX,
        states=("verb_noun", "noun_verb"),
        state_at=("verb_noun", "verb_noun"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10),
    )
