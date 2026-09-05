"""Cost-only adapter for the unchanged FOCUS-2c Amendment 1 science freeze."""

import argparse
import time
from contextlib import contextmanager
from functools import partial
from pathlib import Path
from unittest.mock import patch

from stencil import focus2 as f

CAP_SECONDS = 8 * 3600
FREEZE_COMMIT = "658622149ea6589f5ea68e2d9f07921f0899a3b8"
PILOT_COMMIT = "5a14f4f"
BASE = Path("results/qwen/focus2c/amendment1")
AMENDMENT = Path("results/qwen/focus2c/amendment2")


def pilot_authorization(pre, rows, start, end, audit):
    """Recompute the observed timing prefix; never create a pilot certificate."""
    f.require(
        end["status"] == "INCOMPLETE"
        and end["reason"] == "GPU allocation budget exhausted/projected over cap",
        "not the authorized projected-cost stop",
    )
    f.require(
        start == dict(stage="pilot", binding=pre["binding"], spent_before=pre["spent"])
        and end["binding"] == pre["binding"]
        and end["spent_before"] == pre["spent"],
        "pilot start/end provenance",
    )
    f.require(
        end["record_count"] == len(rows) == 57
        and end["records_hash"]
        == f.digest(
            sorted(rows, key=lambda r: (r["episode"], r["arm"], r["checkpoint"]))
        ),
        "pilot raw records",
    )
    summaries = f.validate_records(
        rows,
        pre["banks"]["pilot"],
        pre["tok"],
        pre["binding"],
        complete=False,
        carried=pre["carried"],
    )
    f.require(
        [s["id"] for s in summaries] == audit["complete_pilot_episodes"]
        and len(summaries) == 2
        and not any(s.get("delay_invalid") for s in summaries),
        "pilot prefix changed",
    )
    allocation = end["spent_after"] - end["spent_before"]
    f.require(
        allocation + 1e-6
        >= end["load_seconds"] + sum(r["cost"]["allocation_seconds"] for r in rows),
        "nonadditive pilot cost",
    )
    new = [r for r in rows if r["episode"] == "pilot:sort:ascending:512:0"]
    first = min(
        r["cost"]["cumulative_seconds"] - r["cost"]["allocation_seconds"] for r in new
    )
    last = max(r["cost"]["cumulative_seconds"] for r in new)
    lower = last - first
    lower_projection = last + 1.25 * (256 * lower + end["load_seconds"])
    f.require(
        audit["status"] == "VERIFIED_BUDGET_STOP"
        and audit["records_hash"] == end["records_hash"]
        and audit["cumulative_gpu_seconds"] == end["spent_after"]
        and audit["observed_new_cell_seconds_lower_bound"] == lower
        and audit["cumulative_plus_final_projection_seconds_lower_bound"]
        == lower_projection
        and lower_projection >= 24481,
        "authorizing timing measurement differs",
    )
    # Total measured non-load stage time bounds the new cell from above.
    # The carried cell must use original generation cost, never replay speed.
    old = list(pre["carried"].values())
    old_span = max(r["cost"]["cumulative_seconds"] for r in old) - min(
        r["cost"]["cumulative_seconds"] - r["cost"]["allocation_seconds"] for r in old
    )
    worst = allocation - end["load_seconds"]
    f.require(worst >= max(lower, old_span), "conservative pilot upper bound")
    return dict(
        spent=end["spent_after"],
        worst_cell_seconds=worst,
        projection=1.25 * (256 * worst + end["load_seconds"]),
        authorizing_projection_lower_bound=lower_projection,
    )


def authorize(receipt_path):
    root = f.ROOT
    receipt_path = Path(receipt_path).resolve()
    raw = f.member(root, "HEAD", str(receipt_path.relative_to(root)))
    receipt = f.parse_json(raw)
    f.require(
        receipt["amendment"] == "FOCUS-2c AMENDMENT 2"
        and receipt["gpu_cap_seconds"] == CAP_SECONDS
        and receipt["freeze_commit"] == FREEZE_COMMIT
        and receipt["output_path"] == str(BASE / "outputs")
        and receipt["new_pilot"] is False,
        "cost amendment receipt",
    )
    for descriptor in receipt["files"].values():
        f.member(root, descriptor["commit"], descriptor["path"], descriptor["sha256"])
    paths = {d["path"] for d in receipt["files"].values()}
    required = {
        str(Path(__file__).resolve().relative_to(root)),
        str(AMENDMENT / "section.md"),
        str(BASE / "pilot-audit.json"),
        str(BASE / "launch-receipt.json"),
        *(
            str(p.relative_to(root))
            for p in (root / BASE / "outputs/pilot").rglob("*.json")
        ),
    }
    f.require(required <= paths, "unbound adapter/amendment/pilot evidence")
    for descriptor in receipt["files"].values():
        if descriptor["path"].startswith(str(BASE / "outputs/pilot")):
            f.require(
                descriptor["commit"]
                == f.git_bytes(root, "rev-parse", PILOT_COMMIT).decode().strip(),
                "pilot evidence must precede amendment",
            )
    pre = f.preflight(
        root / BASE / "freeze",
        root / BASE / "launch-receipt.json",
        "run",
        root / BASE / "outputs",
        certificates=False,
    )
    f.require(pre["binding"]["freeze_commit"] == FREEZE_COMMIT, "science freeze")
    folder = root / BASE / "outputs/pilot"
    f.require(
        not (folder / "certificate.json").exists(), "unexpected pilot certificate"
    )
    costing = pilot_authorization(
        pre,
        f.RecordStore(folder / "records").rows(),
        f.parse_json((folder / "start.json").read_text()),
        f.parse_json((folder / "end.json").read_text()),
        f.parse_json((root / BASE / "pilot-audit.json").read_text()),
    )
    f.require(costing == receipt["costing"], "registered costing differs")
    if costing["spent"] + costing["projection"] >= CAP_SECONDS:
        raise f.Incomplete("cost/projection over amended eight GPU-hour cap")
    pre.update(costing)
    pre["binding"] = {**pre["binding"], "cost_amendment_sha256": f.sha(raw)}
    return pre


@contextmanager
def cost_runtime(pre):
    """Supply authorized cost inputs to the unmodified scheduling consumers."""

    def checked_preflight(folder, launch, stage, output, **kwargs):
        f.require(
            Path(folder).resolve() == f.ROOT / BASE / "freeze"
            and Path(launch).resolve() == f.ROOT / BASE / "launch-receipt.json"
            and Path(output).resolve() == f.ROOT / BASE / "outputs"
            and stage == "run",
            "only the registered unstarted final stage is authorized",
        )
        return pre

    budget_class = f.Budget
    with (
        patch.object(f, "preflight", checked_preflight),
        patch.object(f, "GPU_CAP", CAP_SECONDS),
        patch.object(f, "Budget", partial(budget_class, cap=CAP_SECONDS)),
    ):
        yield


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", required=True, choices=("validate", "run", "analyze"))
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args(argv)
    started = time.monotonic()
    try:
        pre = authorize(args.receipt)
        inputs = (
            f.ROOT / BASE / "freeze",
            f.ROOT / BASE / "launch-receipt.json",
            f.ROOT / BASE / "outputs",
        )
        if args.mode == "validate":
            result = dict(
                status="PASS",
                binding=pre["binding"],
                costing={
                    k: pre[k]
                    for k in (
                        "spent",
                        "projection",
                        "worst_cell_seconds",
                        "authorizing_projection_lower_bound",
                    )
                },
            )
        else:
            with cost_runtime(pre):
                if args.mode == "run":
                    result = f.execute_stage(*inputs, "run")
                else:
                    path = f.ROOT / AMENDMENT / "analysis.json"
                    f.require(not path.exists(), "refusing analysis overwrite")
                    result = f.analyze(*inputs)
                    result["analysis_seconds"] = time.monotonic() - started
                    result["total_charged_seconds"] = (
                        result["allocation_seconds"] + result["analysis_seconds"]
                    )
                    result["gpu_cap_seconds"] = CAP_SECONDS
                    if result["total_charged_seconds"] >= CAP_SECONDS:
                        result["status"] = "INCOMPLETE"
                        result["cost_stop"] = "run plus analyze exceeds amended cap"
                    f.atomic_json(path, result)
        print(f.canonical(result))
        return (
            0
            if result["status"]
            in (
                "COMPLETE",
                "PASS",
                "FAIL",
                "FAIL-SAFETY",
                "PASS with MARGINAL ADDED CONTROL",
            )
            else 1
        )
    except (f.Invalid, f.Incomplete, OSError, KeyError, TypeError, ValueError) as exc:
        print(
            f.canonical(dict(status=getattr(exc, "status", "INVALID"), reason=str(exc)))
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
