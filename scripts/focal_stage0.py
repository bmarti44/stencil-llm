"""Stage 0 (CPU) kill criteria for direction rev 2, focal delivery.

K1: rule typing from the convention sentence agrees with the checker's unit family
    on the public MemoryCode instruction pool (``vendor/memorycode/topics.json``).
K2: the incremental unit-start detector, replayed on the 278 stored Exp 4C outputs,
    fires on every unit start the final AST reports (recall) and never inside
    strings (precision), measured against ``ast`` on the extracted code.

Writes ``results/focal/stage0.json``.  No model, no GPU, no item labels.
"""

from __future__ import annotations

import ast
import glob
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from stencil.focal import FAMILY_KIND, rule_family, unit_starts  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "results/memorycode-long/screen_long_4c-4b-package-role_evicted/raw"
OUT = ROOT / "results/focal/stage0.json"


def k1() -> dict:
    topics = json.loads((ROOT / "vendor/memorycode/topics.json").read_text())
    rows = []
    for ins in topics["instructions"]:
        for text, regex in zip(ins["text"], ins["regex"]):
            fam = regex[0]
            rows.append((text, fam, FAMILY_KIND[fam], rule_family(text)))
    agree = sum(1 for _, _, want, got in rows if want == got)
    errors = [(t, f, w, g) for t, f, w, g in rows if w != g]
    return {"n": len(rows), "agree": agree, "rate": agree / len(rows), "errors": errors}


_FENCE_RE = re.compile(r"```(?:python|py)?\n(.*?)```", re.S)


def _ast_units(code: str) -> Counter:
    """Unit starts by kind from the final AST (line numbers of headers/decorators)."""
    tree = ast.parse(code)
    units: Counter = Counter()
    lines = set()

    class V(ast.NodeVisitor):
        def __init__(self):
            self.cls = 0

        def visit_ClassDef(self, n):
            ln = min([d.lineno for d in n.decorator_list] + [n.lineno])
            units["class"] += 1
            lines.add((ln, "class"))
            self.cls += 1
            self.generic_visit(n)
            self.cls -= 1

        def _def(self, n):
            ln = min([d.lineno for d in n.decorator_list] + [n.lineno])
            kind = "method" if self.cls else "function"
            units[kind] += 1
            lines.add((ln, kind))
            saved, self.cls = self.cls, 0
            self.generic_visit(n)
            self.cls = saved

        visit_FunctionDef = _def
        visit_AsyncFunctionDef = _def

        def visit_Import(self, n):
            units["import"] += 1
            lines.add((n.lineno, "import"))

        visit_ImportFrom = visit_Import

        def visit_Assign(self, n):
            if all(isinstance(t, ast.Name) for t in n.targets):
                units["variable"] += 1
                lines.add((n.lineno, "variable"))
            self.generic_visit(n)

        def visit_AnnAssign(self, n):
            if isinstance(n.target, ast.Name):
                units["variable"] += 1
                lines.add((n.lineno, "variable"))

    V().visit(tree)
    return units, lines


def k2() -> dict:
    files = sorted(glob.glob(str(RAW / "*.json")))
    tot = Counter()
    per_kind_hit: Counter = Counter()
    per_kind_want: Counter = Counter()
    false_fires = 0
    fired_total = 0
    parsable = 0
    unparsable = 0
    for f in files:
        text = json.loads(Path(f).read_text())["generation"]["text"]
        blocks = _FENCE_RE.findall(text)
        code = "\n".join(blocks) if blocks else text
        try:
            _, want_lines = _ast_units(code)
            parsable += 1
        except SyntaxError:
            unparsable += 1
            continue
        # replay the detector on the code exactly as the runtime would see it
        # (the fenced text), then map fired lines to code lines
        fired = unit_starts(text)
        fired_total += len(fired)
        # rebuild a line map from fenced text lines to concatenated-code lines
        code_lines: list[int | None] = []
        in_code = False
        j = 0
        for line in text.split("\n"):
            if re.match(r"^\s*```", line):
                in_code = not in_code
                code_lines.append(None)
                continue
            code_lines.append(j if in_code else None)
            if in_code:
                j += 1
        if not blocks:
            code_lines = list(range(len(text.split("\n"))))
        fired_set = set()
        for u in fired:
            cl = code_lines[u.line] if u.line < len(code_lines) else None
            if cl is None:
                false_fires += 1
                continue
            fired_set.add((cl + 1, u.kind))
        for ln, kind in want_lines:
            per_kind_want[kind] += 1
            if (ln, kind) in fired_set:
                per_kind_hit[kind] += 1
        for key in fired_set:
            if key not in want_lines:
                false_fires += 1
        tot["files"] += 1
    recall = {k: per_kind_hit[k] / per_kind_want[k] for k in per_kind_want}
    return {
        "files": len(files),
        "parsable": parsable,
        "unparsable_skipped": unparsable,
        "want": dict(per_kind_want),
        "hit": dict(per_kind_hit),
        "recall": recall,
        "recall_all": sum(per_kind_hit.values()) / max(1, sum(per_kind_want.values())),
        "fired": fired_total,
        "false_fires": false_fires,
        "precision": 1 - false_fires / max(1, fired_total),
    }


def main() -> None:
    res = {"K1": k1(), "K2": k2()}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=2))
    k1r, k2r = res["K1"], res["K2"]
    print(f"K1 typing agreement {k1r['agree']}/{k1r['n']} = {k1r['rate']:.3f}")
    for e in k1r["errors"][:20]:
        print("  MISS", e)
    print(
        f"K2 files {k2r['files']} parsable {k2r['parsable']} "
        f"recall {k2r['recall_all']:.3f} precision {k2r['precision']:.3f} "
        f"per-kind {k2r['recall']}"
    )


if __name__ == "__main__":
    main()
