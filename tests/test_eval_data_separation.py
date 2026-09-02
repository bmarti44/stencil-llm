"""Forbid evaluation-benchmark data from reaching fitting or selection code."""

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVAL_ONLY = {
    "scripts/bfcl_mt.py",
    "scripts/ledger_eval.py",
    "scripts/ledger_kv_probe.py",
}
FORBIDDEN_PATHS = (
    "data/bench/",
    "results/qwen/b4-multiif-base",
)
FIT_NAME = re.compile(
    r"(?:^|_)(?:fit(?:ting)?|train(?:ing)?|refit(?:ting)?|oracle)(?:_|$)"
)
LOAD_DOCS_NAME = re.compile(r"load_.*_docs$")


def _is_fitting_name(name: str) -> bool:
    if name.startswith("eval_"):
        return False
    return bool(
        FIT_NAME.search(name)
        or name in {"select_policy", "training_docs"}
        or LOAD_DOCS_NAME.search(name)
    )


def _called_functions(node: ast.AST) -> set[str]:
    called = set()
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        if isinstance(child.func, ast.Name):
            called.add(child.func.id)
        elif isinstance(child.func, ast.Attribute):
            called.add(child.func.attr)
    return called


def _joined_path(node: ast.AST) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value.strip("/")
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        sides = (_joined_path(node.left), _joined_path(node.right))
        return "/".join(
            piece for piece in sides if piece
        )
    return ""


def _path_refs(node: ast.AST) -> set[str]:
    refs = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Constant) and isinstance(child.value, str):
            refs.update(path for path in FORBIDDEN_PATHS if path in child.value)
        if isinstance(child, ast.BinOp) and isinstance(child.op, ast.Div):
            joined = _joined_path(child) + "/"
            refs.update(path for path in FORBIDDEN_PATHS if path in joined)
    return refs


def _violations(path: Path) -> list[str]:
    rel = path.relative_to(ROOT).as_posix()
    if rel in EVAL_ONLY:
        return []
    tree = ast.parse(path.read_text(), filename=rel)
    functions = {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    calls = {
        name: _called_functions(node) & functions.keys()
        for name, node in functions.items()
    }
    direct_refs = {name: _path_refs(node) for name, node in functions.items()}

    # Propagate benchmark references through local helper calls. This catches a
    # clean-looking ``training_docs`` wrapper that delegates to an eval loader.
    reachable_refs = {name: set(refs) for name, refs in direct_refs.items()}
    changed = True
    while changed:
        changed = False
        for name, callees in calls.items():
            inherited = set().union(*(reachable_refs[callee] for callee in callees))
            if not inherited <= reachable_refs[name]:
                reachable_refs[name].update(inherited)
                changed = True

    problems = []
    for name in sorted(functions):
        if _is_fitting_name(name) and reachable_refs[name]:
            problems.append(f"{rel}:{name} -> {sorted(reachable_refs[name])}")

    if _is_fitting_name(path.stem):
        refs = _path_refs(tree)
        if refs:
            problems.append(f"{rel}:module -> {sorted(refs)}")
    return problems


def test_evaluation_data_never_reaches_fitting_or_selection_code():
    files = sorted((ROOT / "src" / "stencil").glob("*.py"))
    files += sorted((ROOT / "scripts").glob("*.py"))
    problems = [problem for path in files for problem in _violations(path)]
    assert not problems, "evaluation data used by fitting code:\n" + "\n".join(problems)


def test_split_path_literals_are_recognized():
    tree = ast.parse('ROOT / "data" / "bench" / "hidden.jsonl"')
    assert _path_refs(tree) == {"data/bench/"}
