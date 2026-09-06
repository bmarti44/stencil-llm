"""CPU-only sensitivity audit: preserve NaN/undefined/holes in return values.

The frozen scorer JSON-normalizes cross-realm return values. This independent
stricter comparison uses structuredClone before deepStrictEqual, with no model
reruns, task changes, or changes to the registered primary endpoint.
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import focus_check40k as k  # noqa: E402


def evaluate(code, task):
    node = k.NODE.replace(
        "JSON.parse(JSON.stringify(value)),t.expected",
        "structuredClone(value),t.expected",
    )
    assert node != k.NODE
    proc = subprocess.run(
        ["node", "-e", node],
        input=json.dumps(
            dict(
                code=code,
                name=task["name"],
                tests=task["tests"],
                no_mutation="mutat" in task["prompt"],
            )
        ),
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def main():
    fixture = dict(name="f", prompt="", tests=[dict(args=[], expected=None)])
    assert not evaluate("function f(){return NaN}", fixture)[0]["pass"]
    assert evaluate("function f(){return null}", fixture)[0]["pass"]
    by = {t["id"]: t for t in k.bank()}
    refs = json.loads((k.OUT / "reference-solutions.json").read_text())
    for task in by.values():
        assert all(x["pass"] for x in evaluate(refs[task["id"]], task))
    rows = [json.loads(s) for s in (k.OUT / "records.jsonl").read_text().splitlines()]
    changes, strict_rows, results = [], [], []
    for row in rows:
        task = by[row["task_id"]]
        code, _ = k.base.extract_code(row["text"])
        tests = evaluate(code, task)
        success = all(x["pass"] for x in tests)
        results.append(
            dict(id=row["id"], success=success, tests=[x["pass"] for x in tests])
        )
        if results[-1]["tests"] != [x["pass"] for x in row["score"]["tests"]]:
            changes.append(
                dict(
                    id=row["id"],
                    task=row["task_id"],
                    original_success=row["score"]["success"],
                    strict_success=success,
                    tests=tests,
                )
            )
        strict_rows.append(dict(row, score=dict(row["score"], success=success)))
    summary = json.loads((k.OUT / "summary.json").read_text())
    out = dict(
        records=len(rows),
        reference_tests=160,
        nan_distinguished=True,
        changes=changes,
        per_record=results,
        summary=k.summarize(strict_rows, summary["complete"]),
    )
    k.write("strict-audit.json", out)
    print(
        json.dumps(
            dict(
                records=len(rows),
                differences=len(changes),
                reading=out["summary"]["reading"],
            )
        )
    )


if __name__ == "__main__":
    main()
