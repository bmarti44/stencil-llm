"""AST deterrent for accidental rule-text interpretation, not a proof.

This syntax scan cannot track aliases, dynamic dispatch, arbitrary equality,
slicing, pattern matching or disguised container names. The explicit module
allowlist and runtime golden episode complement it; completeness is not claimed.
"""

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
                part in {"re", "operator", "fnmatch", "difflib", "importlib"}
                or part.startswith("focus3")
                for name in names
                for part in name.split(".")
            ):
                bad.append(node.lineno)
        if isinstance(node, ast.Name) and node.id in {
            "re",
            "operator",
            "fnmatch",
            "difflib",
            "importlib",
            "__import__",
        }:
            bad.append(node.lineno)
        if isinstance(node, ast.Attribute) and node.attr in {
            "count",
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
    for module in ("__init__", "register", "renderer", "loop", "journal"):
        path = ROOT / "src/stencil/focus" / f"{module}.py"
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
        "entry.text.count('cancel')",
        "entry.text.startswith('cancel')",
        "entry.text.endswith('cancel')",
        "import fnmatch; fnmatch.fnmatch(entry.text, '*cancel*')",
        "import importlib; importlib.import_module('re')",
        "__import__('re')",
        "import operator; operator.contains(entry.text, 'cancel')",
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
    import sys

    from stencil import focus3
    from stencil.focus import Verdict
    from tests.test_focus_episode import test_whole_episode_bytes_state_and_journal

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
        original = getattr(focus3, name)
        # Also replace aliases already bound by `from ... import ...`.
        for module_name, module in tuple(sys.modules.items()):
            if module_name == "stencil.focus" or module_name.startswith(
                "stencil.focus."
            ):
                for attr, value in tuple(vars(module).items()):
                    if value is original:
                        monkeypatch.setattr(module, attr, forbidden)
        monkeypatch.setattr(focus3, name, forbidden)
        with pytest.raises(pytest.fail.Exception, match="legacy regex binder"):
            getattr(focus3, name)("probe")
    test_whole_episode_bytes_state_and_journal(tmp_path, Verdict.ABSTAIN)
