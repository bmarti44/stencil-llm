"""Refuse to launch an evaluation whose adapter the runner would reject.

a_screen_run.py validates the training log's recorded hashes against the CURRENT
files (trainer, a_screen, a_train_pool, trunk) and against the frozen pools.
Every one of those is a file I might edit between training and evaluation, and
the failure arrives only after the GPU hours are spent -- which is exactly how
the minimum-duration guard would have cost four hours.  This checks the same
things first, in a second, on the CPU.

Rewritten 2026-09-13 after Astra's back-on-track review found the guard passing
on things it was built to catch.  Its 13/13 mutation run established nothing,
because with synthetic metadata it accepted

  * an SFT objective sitting in the CF directory -- nothing tied the log's
    `objective` to the arm the caller intended, so a mislabelled or overwritten
    directory would have been evaluated as the other arm;
  * a log with no `hub` field at all -- the trunk check read `ident.get("hub")`
    and simply did not run when it was absent;
  * two logs missing the same field in `--compare`, because `None == None`, so
    every absent field counted as agreement.

The rule this version follows: a check that cannot run is a FAILURE, never a
pass.  `need()` asserts presence before any comparison, the caller must name the
arm it believes it is evaluating, and `--compare` runs the full individual
validation on both adapters before it looks at them side by side.

    python preflight.py check   <dir> --arm cf  [--require-steps N] [--hub PATH]
    python preflight.py compare <dir> <dir> --arms sft cf [--hub PATH]
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path("/home/bmarti44/stencil-llm")
sys.path.insert(0, str(ROOT / "src"))
from stencil import a_screen as A  # noqa: E402

REGISTERED = {
    "seed": 0, "lr": 1e-4, "rank": 16, "alpha": 32,
    "beta": 0.1, "dpo_weight": 0.1, "accum": 8,
}
REGISTERED_BUDGET_S = 4 * 3600
ARMS = ("sft", "cf")
HASH_FIELDS = (
    ("trainer_sha256", ROOT / "scripts/a_screen_train.py"),
    ("a_screen_sha256", ROOT / "src/stencil/a_screen.py"),
    ("a_train_pool_sha256", ROOT / "src/stencil/a_train_pool.py"),
)
SHARED_IDENTITY = ("trainer_sha256", "a_screen_sha256", "a_train_pool_sha256",
                   "hub", "hub_sha256", "train_pool_sha256")


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def need(d, key, bad, where):
    """Presence first.  A missing field is a refusal, never a silent agreement."""
    if key not in d or d[key] is None:
        bad.append(f"{where}: {key} is missing")
        return None
    return d[key]


def check(adapter: str, arm: str, require_steps: int = 0, hub: str = "") -> list[str]:
    """Problems with one adapter.  Empty list means eligible."""
    bad: list[str] = []
    if arm not in ARMS:
        return [f"{arm!r} is not one of {ARMS}"]
    path = Path(adapter) / "train-log.json"
    if not path.exists():
        return [f"{path} does not exist"]
    try:
        log = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        return [f"{path} is not valid JSON ({e})"]
    ident = log.get("identity")
    if not isinstance(ident, dict):
        return [f"{path} has no identity block"]

    # the arm the caller believes it is evaluating, bound to the log AND the directory
    objective = need(log, "objective", bad, "log")
    if objective is not None and objective != arm:
        bad.append(f"objective {objective!r} but the caller asked for {arm!r}")
    if Path(adapter).name != arm:
        bad.append(f"directory {Path(adapter).name!r} does not name the {arm!r} arm")

    if not (log.get("final") and log.get("status") == "complete"):
        bad.append(f"final={log.get('final')} status={log.get('status')!r}")
    steps = need(log, "steps", bad, "log")
    if steps is not None and (not isinstance(steps, int) or steps < 1):
        bad.append(f"steps={steps!r}")
    if require_steps and steps != require_steps:
        bad.append(f"steps {steps} != matched {require_steps}")
    if need(log, "budget_seconds", bad, "log") not in (None, REGISTERED_BUDGET_S):
        bad.append(f"budget_seconds={log.get('budget_seconds')}")
    if ident.get("limit"):
        bad.append(f"limit={ident['limit']}")
    if need(log, "examples", bad, "log") == 0:
        bad.append("examples=0")

    for k, want in REGISTERED.items():
        if need(log, k, bad, "log") not in (None, want):
            bad.append(f"{k}={log.get(k)!r} != {want!r}")

    for field, file in HASH_FIELDS:
        trained = need(ident, field, bad, "identity")
        if trained is None:
            continue
        cur = sha(file.read_text())
        if trained != cur:
            bad.append(f"{field}: trained {trained}, current {cur} ({file.name})")

    trunk = need(ident, "hub", bad, "identity")
    trunk_sha = need(ident, "hub_sha256", bad, "identity")
    if trunk is not None:
        if hub and str(Path(hub)) != str(Path(trunk)):
            bad.append(f"trained on trunk {trunk}, evaluating on {hub}")
        on_disk = Path(trunk)
        if not on_disk.is_dir():
            bad.append(f"the trunk {trunk} is not on disk")
        elif trunk_sha is not None and trunk_sha != A.dir_sha(on_disk):
            bad.append("hub_sha256 differs from the trunk on disk")

    pool = need(ident, "train_pool_sha256", bad, "identity")
    frozen = json.loads(
        (ROOT / "results/a-screen/train-pool.json").read_text()
    )["pool_sha256"]
    if pool is not None and pool != frozen:
        bad.append(f"TRAIN pool {pool} != frozen {frozen}")

    weights = Path(adapter) / "adapter_model.safetensors"
    if not weights.exists():
        bad.append("adapter_model.safetensors is missing")
    return bad


def compare(a_dir: str, b_dir: str, arms, hub: str = "") -> list[str]:
    """Both adapters individually eligible does NOT make them comparable.

    The peer's point, and it is right: a set of invariants only bounds the axes
    it thinks to assert.  Every check above is one-sided -- "this adapter is a
    valid adapter" -- and none of them looks at the OTHER arm, so two adapters
    could each pass while differing in step count, data, recipe or trunk.  That
    is the axis that decides whether cf-vs-sft means anything, so it is asserted
    here -- and the individual validation is run first, because two adapters
    that agree with each other and with nothing else are not a comparison."""
    bad = []
    for d, arm in zip((a_dir, b_dir), arms):
        bad += [f"{arm}: {p}" for p in check(d, arm, hub=hub)]
    la = json.loads((Path(a_dir) / "train-log.json").read_text())
    lb = json.loads((Path(b_dir) / "train-log.json").read_text())
    ia, ib = la.get("identity", {}), lb.get("identity", {})

    for k in ("steps", "examples"):
        va, vb = need(la, k, bad, arms[0]), need(lb, k, bad, arms[1])
        if va is not None and vb is not None and va != vb:
            note = " -- NOT step-matched" if k == "steps" else ""
            bad.append(f"{k} {va} vs {vb}{note}")
    oa, ob = need(la, "objective", bad, arms[0]), need(lb, "objective", bad, arms[1])
    if oa is not None and oa == ob:
        bad.append(f"both objectives are {oa!r} -- not a contrast")
    for k in REGISTERED:
        va, vb = need(la, k, bad, arms[0]), need(lb, k, bad, arms[1])
        if va is not None and vb is not None and va != vb:
            bad.append(f"{k}: {va!r} vs {vb!r}")
    for k in SHARED_IDENTITY:
        va, vb = need(ia, k, bad, f"{arms[0]}.identity"), need(ib, k, bad,
                                                              f"{arms[1]}.identity")
        if va is not None and vb is not None and va != vb:
            bad.append(f"{k} differs between arms: {va!r} vs {vb!r}")
    return bad


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("adapter")
    c.add_argument("--arm", required=True, choices=ARMS)
    c.add_argument("--require-steps", type=int, default=0)
    c.add_argument("--hub", default="")
    m = sub.add_parser("compare")
    m.add_argument("adapters", nargs=2)
    m.add_argument("--arms", nargs=2, required=True, choices=ARMS)
    m.add_argument("--hub", default="")
    a = ap.parse_args(argv)

    if a.cmd == "check":
        bad = check(a.adapter, a.arm, a.require_steps, a.hub)
        if bad:
            print(f"REFUSE {a.arm}: " + "; ".join(bad))
            return 1
        log = json.loads((Path(a.adapter) / "train-log.json").read_text())
        print(f"OK {a.arm}: {log['steps']} optimizer steps over {log['examples']} "
              f"examples, status complete, every hash current")
        return 0

    if a.arms[0] == a.arms[1]:
        print(f"NOT COMPARABLE: both arms named {a.arms[0]!r}")
        return 1
    bad = compare(a.adapters[0], a.adapters[1], a.arms, a.hub)
    if bad:
        print("NOT COMPARABLE: " + "; ".join(bad))
        return 1
    la = json.loads((Path(a.adapters[0]) / "train-log.json").read_text())
    print(f"COMPARABLE: both {la['steps']} steps over {la['examples']} examples, "
          f"same recipe, same trunk, same pools; objectives "
          f"{a.arms[0]!r} vs {a.arms[1]!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
