"""Explicit controller fence: no legacy imports or rule-text interpretation."""

import ast
import importlib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def violations(source):
    tree = ast.parse(source)
    bad = []
    # Membership is allowed only against visibly structured containers or the
    # declared metadata collections below. Unknown/aliased text fails closed.
    containers = {
        "AUTHORITY",
        "REQUEST_KINDS",
        "ids",
        "explicit_keys",
        "allowed",
        "retired",
    }
    attributes = {"task_handles", "request_kinds"}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [n.name for n in node.names]
            if isinstance(node, ast.ImportFrom):
                names.append(node.module or "")
            if any(
                part == "re" or part.startswith("focus3")
                for name in names
                for part in name.split(".")
            ):
                bad.append(node.lineno)
        if isinstance(node, ast.Name) and node.id == "re":
            bad.append(node.lineno)
        if isinstance(node, ast.Attribute) and node.attr in {
            "find",
            "rfind",
            "index",
            "rindex",
            "startswith",
            "endswith",
            "lower",
            "upper",
            "casefold",
            "__contains__",
        }:
            # This one is a typed Version lookup, not string interpretation.
            if not (
                node.attr == "index" and ast.unparse(node.value) == "self.versions"
            ):
                bad.append(node.lineno)
        if isinstance(node, ast.Compare):
            for op, rhs in zip(node.ops, node.comparators, strict=True):
                if isinstance(op, (ast.In, ast.NotIn)):
                    structured = isinstance(
                        rhs, (ast.Set, ast.Tuple, ast.List, ast.Dict)
                    )
                    declared = isinstance(rhs, ast.Name) and rhs.id in containers
                    metadata = isinstance(rhs, ast.Attribute) and rhs.attr in attributes
                    rule_text = any(
                        isinstance(part, ast.Attribute)
                        and part.attr in {"text", "value"}
                        for operand in (node.left, rhs)
                        for part in ast.walk(operand)
                    )
                    if rule_text or not (structured or declared or metadata):
                        bad.append(node.lineno)
    return bad


def test_all_explicit_modules_import_and_pass_ast_fence():
    for path in sorted((ROOT / "src/stencil/focus").rglob("*.py")):
        relative = path.relative_to(ROOT / "src").with_suffix("")
        name = ".".join(relative.parts)
        importlib.import_module(name)
        assert not violations(path.read_text()), path


@pytest.mark.parametrize(
    "source",
    [
        "import re as regex",
        "from re import search",
        "from stencil import focus3",
        "from stencil.focus3_legacy import scope_of",
        "re.search('a', text)",
        "entry.text.find('cancel')",
        "'cancel' in entry.text",
        "'json' in rule",
        "text = entry.value\n'JSON' in text",
        "entry.text.lower()",
        "entry.text in {'JSON', 'cancel'}",
    ],
)
def test_ast_fence_rejects_regex_and_text_heuristics(source):
    assert violations(source)


def test_explicit_path_never_calls_legacy_helpers(monkeypatch, tmp_path):
    from stencil import focus3
    from stencil.focus import generate_once
    from tests.test_focus_composition import entry, message, session

    def forbidden(*args, **kwargs):
        pytest.fail("explicit path reached legacy regex binder")

    for name in (
        "scope_of",
        "kind_of",
        "request_kind",
        "selected_task",
        "cancellation_message",
        "relation_key",
        "task_switch_only",
    ):
        monkeypatch.setattr(focus3, name, forbidden)
    s = session(tmp_path)
    generate_once(s, [message(entry())], lambda r: "ok")
    generate_once(s, [message(entry("cancels", target=1, eid="c"))], lambda r: "ok")
    generate_once(s, [message(entry("reinstates", target=1, eid="r"))], lambda r: "ok")
    assert s.register.live_mask == (False, True)
