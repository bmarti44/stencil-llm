#!/bin/bash
# Exp 4C evaluation (REGISTRATION-4C.md): the single package-path run over the frozen
# items-4c.json, resumed across ≤55-min slices; ceiling = 3 t_max N from the frozen manifest.
set -u
export STENCIL_GPU_SHARE=1
R=/home/bmarti44/stencil-llm; cd $R
LOG=${STENCIL_LOG_DIR:-$R/results/memorycode-long/logs}; mkdir -p $LOG
F=$R/results/memorycode-long/items-4c.json
Q=$R/results/memorycode-long/qualification-4c.json
[ -f $F ] && [ -f $Q ] || { echo "frozen manifest or qualification missing" >> $LOG/exp4c-eval.log; exit 1; }
read -r N TMAX CEIL SPLIT <<< "$($R/.venv/bin/python - "$F" "$Q" <<'PY'
import json, sys
f = json.load(open(sys.argv[1])); q = json.load(open(sys.argv[2]))
assert q["eligible"], "qualification not eligible"
n = f["n"]; t = f["t_max_seconds"]
print(n, t, 3 * t * n, f["items"][0]["split"])
PY
)"
D=$R/results/memorycode-long/${SPLIT}-4b-package-role_evicted
complete() { $R/.venv/bin/python - "$D" "$F" <<'PY'
import json, sys, pathlib
d = pathlib.Path(sys.argv[1]); ids = [it["id"] for it in json.load(open(sys.argv[2]))["items"]]
n = 0
for i in ids:
    p = d / f"item-{i}.json"
    if p.exists():
        r = json.loads(p.read_text())
        if all(a in r["arms"] for a in ("base", "focus")): n += 1
print(n)
PY
}
echo "eval start N=$N t_max=$TMAX ceiling=$CEIL $(date -u +%FT%TZ)" >> $LOG/exp4c-eval.log
for i in $(seq 1 14); do
  [ "$(complete)" -ge "$N" ] && break
  [ -f $D/BUDGET_EXHAUSTED.json ] && { echo "ceiling reached $(date -u +%FT%TZ)" >> $LOG/exp4c-eval.log; break; }
  until ! grep -q '"name":"stencil-' ~/.gb10-gpu.reservations 2>/dev/null; do sleep 30; done
  bash $R/tools/gpu_reserve.sh stencil-exp4c-eval-$i 55 32 -- $R/.venv/bin/python $R/scripts/memorycode_package_run.py --items-file $F --budget-minutes 50 --ceiling-seconds $CEIL >> $LOG/exp4c-eval.log 2>&1
  echo "slice $i exit=$? $(date -u +%FT%TZ) complete=$(complete)/$N" >> $LOG/exp4c-eval.log
done
echo "eval queue finished $(date -u +%FT%TZ) complete=$(complete)/$N" >> $LOG/exp4c-eval.log
touch $LOG/exp4c-eval.done
