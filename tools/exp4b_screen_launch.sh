#!/bin/bash
# Exp 4B SCREEN-LONG at Qwen3-4B: launches ONLY when the SETUP-LONG qualification object
# reads PASSED (REGISTRATION-4B.md amendment 1, item 3). Ceiling 18,294.371410176158 s.
set -u
export STENCIL_GPU_SHARE=1
R=/home/bmarti44/stencil-llm; cd $R
SP=${STENCIL_LOG_DIR:-/home/bmarti44/stencil-llm/results/memorycode-long/logs}; mkdir -p $SP
D=$R/results/memorycode-long/screen_long-4b-role_evicted
Q=$R/results/memorycode-long/setup_long-4b-role_evicted/summary.json
status=$($R/.venv/bin/python -c "import json,sys; print(json.load(open(sys.argv[1])).get('qualification',{}).get('status'))" $Q)
if [ "$status" != "PASSED" ]; then
  echo "refusing to launch SCREEN: qualification status=$status $(date -u +%FT%TZ)" >> $SP/exp4b-screen.log
  touch $SP/exp4b-screen.done; exit 1
fi
complete() { $R/.venv/bin/python - "$D" <<'PY'
import json, sys, pathlib
d = pathlib.Path(sys.argv[1]); n = 0
for p in d.glob("item-*.json"):
    r = json.loads(p.read_text())
    if all(a in r["arms"] for a in ("base", "focus")): n += 1
print(n)
PY
}
for i in $(seq 1 12); do
  [ "$(complete)" -ge 128 ] && break
  [ -f $D/BUDGET_EXHAUSTED.json ] && { echo "ceiling reached; stopping $(date -u +%FT%TZ)" >> $SP/exp4b-screen.log; break; }
  until ! grep -q '"name":"stencil-' ~/.gb10-gpu.reservations 2>/dev/null; do sleep 30; done
  bash $R/tools/gpu_reserve.sh stencil-exp4b-screen-$i 55 32 -- $R/.venv/bin/python $R/scripts/memorycode_screen.py run --cohort long --split screen_long --model 4b --budget-minutes 50 --ceiling-seconds 18294.371410176158 >> $SP/exp4b-screen.log 2>&1
  echo "4b screen slice $i exit=$? $(date -u +%FT%TZ) complete=$(complete)" >> $SP/exp4b-screen.log
done
echo "4b screen queue finished $(date -u +%FT%TZ) complete=$(complete)" >> $SP/exp4b-screen.log
touch $SP/exp4b-screen.done
