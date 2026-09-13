"""Health of a running cf training, across every metric visible mid-run.

Brian: "if the run is not on a healthy trajectory for all metrics, cancel it."
So the criteria are written down rather than judged in the moment, and a failure
must persist for two consecutive checks before it counts -- one noisy reading is
not a trajectory.

Prints nothing while healthy.  Prints HEALTH FAIL with the reasons when it is
not.

WHAT IT DOES NOT SAY (Astra, 2026-09-13).  These are OPERATIONAL signals only: a
falling loss and a rising margin say the optimiser is working on the training
distribution, and say nothing whatever about whether the adapter transfers to
the screen.  The memory check reads the LARGEST GPU process, not specifically
the owned trainer, so with a co-resident peer it is an upper bound on our usage
rather than a measurement of it.  A run that stays silent here is a run worth
finishing, not a run worth believing.

The cf run this was written for finished on 2026-09-13 (134 steps, complete).
Kept for the next training run; not expanded while GPU work is paused."""

import json
import re
import subprocess
import sys
from pathlib import Path

LOG = Path("/home/bmarti44/stencil-llm/results/a-screen/adapters/cf.log")
SCRATCH = "/tmp/claude-1000/-home-bmarti44-stencil-llm"
STATE = Path(
    f"{SCRATCH}/14c2306d-603f-4fa8-b992-19e1aefb2f05/scratchpad/health-state.json"
)
STEP = re.compile(
    r"^step (\d+) loss ([\d.]+) ce ([\d.]+) margin ([+-][\d.]+) micro (\d+) "
    r"(\d+)s/(\d+)s"
)
# below this the exposure is too thin for the screen to mean anything
MIN_USEFUL_STEPS = 40


def readings():
    out = []
    for line in LOG.read_text(errors="ignore").splitlines():
        m = STEP.match(line.strip())
        if m:
            out.append({
                "step": int(m.group(1)), "loss": float(m.group(2)),
                "ce": float(m.group(3)), "margin": float(m.group(4)),
                "elapsed": int(m.group(6)), "budget": int(m.group(7)),
            })
    return out


def main() -> int:
    alive = subprocess.run(
        ["pgrep", "-f", "a_screen_train.py --objective cf"], capture_output=True
    ).returncode == 0
    r = readings()
    bad = []
    if not r:
        return 0  # nothing to judge yet; the other watch covers a death
    last = r[-1]
    # 1. the preference term must still separate the two golds
    if last["margin"] <= 0:
        bad.append(f"margin {last['margin']:+.3f} is not positive")
    if len(r) >= 3 and r[-1]["margin"] < r[-3]["margin"] * 0.5:
        bad.append(
            f"margin collapsing: {r[-3]['margin']:+.3f} -> {last['margin']:+.3f}"
        )
    # 2. the language-model term must not diverge
    if len(r) >= 3 and last["ce"] > r[-3]["ce"] * 3 and last["ce"] > 0.5:
        bad.append(f"ce diverging: {r[-3]['ce']:.4f} -> {last['ce']:.4f}")
    if last["ce"] != last["ce"] or last["loss"] != last["loss"]:
        bad.append("loss or ce is NaN")
    # 3. the run must still buy enough exposure to be worth finishing
    if len(r) >= 2:
        per = (r[-1]["elapsed"] - r[-2]["elapsed"]) / max(
            r[-1]["step"] - r[-2]["step"], 1
        )
        left = last["budget"] - last["elapsed"]
        projected = last["step"] + int(left / per) if per > 0 else last["step"]
        if projected < MIN_USEFUL_STEPS:
            bad.append(
                f"projected {projected} steps at {per:.0f}s/step, "
                f"under {MIN_USEFUL_STEPS}"
            )
    # 4. memory must be flat, not climbing without bound
    try:
        mib = max(
            int(x.split(",")[1])
            for x in subprocess.run(
                ["nvidia-smi", "--query-compute-apps=pid,used_memory",
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True).stdout.strip().splitlines()
            if x.strip()
        )
        if mib > 75 * 1024:
            bad.append(f"memory {mib} MiB above the 75 GiB bound")
    except Exception:
        pass
    if not alive:
        return 0  # the completion watch owns this case
    prev = json.loads(STATE.read_text()) if STATE.exists() else {"fails": []}
    if bad:
        if prev.get("fails"):
            print(f"HEALTH FAIL (twice running) at step {last['step']}: "
                  + "; ".join(bad))
            print(f"  latest: loss {last['loss']:.4f} ce {last['ce']:.4f} "
                  f"margin {last['margin']:+.3f} {last['elapsed']}s/{last['budget']}s")
            STATE.write_text(json.dumps({"fails": []}))
            return 1
        STATE.write_text(json.dumps({"fails": bad}))
    else:
        STATE.write_text(json.dumps({"fails": []}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
