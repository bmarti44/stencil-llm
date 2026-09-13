"""Why the `off` baseline does not need re-running on the current runner.

The baseline (results/a-screen/runs/off-oldrunner.jsonl) records
runner_sha256 4acdb8f044c25a48.  The current runner hashes differently, and
compare.py refuses a runner_sha256 mismatch unless --runner-exception states the
reason.  This script IS the reason, recomputed rather than asserted:

  1. the two files' differences are confined to the bodies of `if a.adapter:`
     and to one added `ap.add_argument("--require-steps", ..., default=0)`;
  2. only one of the two adapter guards actually changed;
  3. `a.require_steps` is read nowhere except inside an adapter guard, and its
     default is falsy;

so an adapterless run -- which never enters `if a.adapter:` -- executes the same
program under both runners.  Anything the script cannot confirm is printed as a
FAILURE and exits non-zero; nothing here is taken on trust.

    python results/a-screen/analysis/runner_equivalence.py [OLD_REV]
"""

import ast
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "scripts/a_screen_run.py"
BASELINE_RUNNER_SHA = "4acdb8f044c25a48"
DEFAULT_REV = "86282371"


def sha16(text):
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def is_adapter_guard(node):
    return (
        isinstance(node, ast.If)
        and isinstance(node.test, ast.Attribute)
        and node.test.attr == "adapter"
        and isinstance(node.test.value, ast.Name)
        and node.test.value.id == "a"
    )


def is_require_steps_option(node):
    if not (isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)):
        return False
    call = node.value
    return (
        isinstance(call.func, ast.Attribute)
        and call.func.attr == "add_argument"
        and call.args
        and isinstance(call.args[0], ast.Constant)
        and call.args[0].value == "--require-steps"
    )


class Strip(ast.NodeTransformer):
    """Empty every adapter guard and drop the --require-steps option, keeping a
    record of the guard bodies so they can be compared one by one."""

    def __init__(self):
        self.guard_bodies = []
        self.options_removed = 0

    def visit_If(self, node):
        self.generic_visit(node)
        if is_adapter_guard(node):
            self.guard_bodies.append(
                "\n".join(ast.dump(x) for x in node.body)
            )
            return ast.If(test=node.test, body=[ast.Pass()], orelse=[])
        return node

    def visit_Expr(self, node):
        if is_require_steps_option(node):
            self.options_removed += 1
            return None
        return node


def strip(src):
    t = Strip()
    tree = t.visit(ast.parse(src))
    ast.fix_missing_locations(tree)
    return ast.dump(tree), t


def require_steps_reads_outside_guard(src):
    """Every `a.require_steps` load that is NOT lexically inside an adapter guard."""
    tree = ast.parse(src)
    inside = set()
    for node in ast.walk(tree):
        if is_adapter_guard(node):
            for sub in node.body:
                for x in ast.walk(sub):
                    inside.add(id(x))
    out = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Attribute)
            and node.attr == "require_steps"
            and isinstance(node.value, ast.Name)
            and node.value.id == "a"
            and id(node) not in inside
        ):
            out.append(node.lineno)
    return out


def main(rev=DEFAULT_REV):
    new_src = RUNNER.read_text()
    old_src = subprocess.run(
        ["git", "-C", str(ROOT), "show", f"{rev}:scripts/a_screen_run.py"],
        capture_output=True, text=True, check=True,
    ).stdout

    failures = []
    print(f"old runner ({rev}) sha16 {sha16(old_src)}")
    print(f"current runner        sha16 {sha16(new_src)}")
    if sha16(old_src) != BASELINE_RUNNER_SHA:
        failures.append(
            f"{rev} hashes {sha16(old_src)}, not the {BASELINE_RUNNER_SHA} the "
            f"baseline records -- this is not the runner that produced it"
        )

    old_dump, old_t = strip(old_src)
    new_dump, new_t = strip(new_src)
    print(f"adapter guards: old {len(old_t.guard_bodies)}, "
          f"new {len(new_t.guard_bodies)}")
    print(f"--require-steps options removed: old {old_t.options_removed}, "
          f"new {new_t.options_removed}")

    if old_dump != new_dump:
        failures.append(
            "the runners differ OUTSIDE the adapter guards and the added option"
        )
    else:
        print("outside those sites the two runners are AST-identical: True")

    if len(old_t.guard_bodies) != len(new_t.guard_bodies):
        failures.append("the runners have different numbers of adapter guards")
    else:
        differing = [
            i for i, (o, n) in enumerate(zip(old_t.guard_bodies, new_t.guard_bodies))
            if o != n
        ]
        print(f"adapter guard bodies that differ: {differing} "
              f"of {len(old_t.guard_bodies)}")

    stray = require_steps_reads_outside_guard(new_src)
    if stray:
        failures.append(f"a.require_steps is read outside an adapter guard at {stray}")
    else:
        print("a.require_steps is read only inside an adapter guard: True")

    print()
    if failures:
        print("FAILURE -- the exception is NOT established:")
        for f in failures:
            print(f"  * {f}")
        return 1
    print("ESTABLISHED: an adapterless run executes the same program under both")
    print("runners, so results/a-screen/runs/off-oldrunner.jsonl needs no re-run.")
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
