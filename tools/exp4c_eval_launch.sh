#!/bin/bash
# Exp 4C evaluation (REGISTRATION-4C.md): the single package-path run over the frozen
# items-4c.json, resumed across <=55-min reservations with a 50-min (3,000 s) per-process
# resident limit enforced by the runner's watchdog. Every status is checked explicitly:
# a configuration/chain failure or a runner failure stops the queue (review finding 3).
set -u
export STENCIL_GPU_SHARE=1
R=/home/bmarti44/stencil-llm; cd $R
LOG=${STENCIL_LOG_DIR:-$R/results/memorycode-long/logs}; mkdir -p $LOG
F=$R/results/memorycode-long/items-4c.json
Q=$R/results/memorycode-long/qualification-4c.json
PY=$R/.venv/bin/python
[ -f $F ] && [ -f $Q ] || { echo "frozen manifest or qualification missing" >> $LOG/exp4c-eval.log; exit 1; }
CHAIN=$($PY - "$F" "$Q" <<'PYEOF'
import json, sys, importlib.util, hashlib, pathlib
root = pathlib.Path("/home/bmarti44/stencil-llm")
spec = importlib.util.spec_from_file_location("i", root / "scripts/memorycode_4c_items.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
f = json.load(open(sys.argv[1])); q = json.load(open(sys.argv[2]))
sha = hashlib.sha256(open(sys.argv[2], "rb").read()).hexdigest()
problems = m.verify_frozen(f, q, sha)
if problems:
    print("CHAIN-BROKEN " + "; ".join(problems)); sys.exit(1)
print(f["n"], f["t_max_seconds"], 3 * f["t_max_seconds"] * f["n"], f["items"][0]["split"])
PYEOF
)
chain_status=$?
echo "chain: $CHAIN" >> $LOG/exp4c-eval.log
[ $chain_status -eq 0 ] || { echo "chain check failed; not launching" >> $LOG/exp4c-eval.log; touch $LOG/exp4c-eval.done; exit 1; }
read -r N TMAX CEIL SPLIT <<< "$CHAIN"
D=$R/results/memorycode-long/${SPLIT}-4b-package-role_evicted
complete() { $PY - "$D" "$F" <<'PYEOF'
import json, sys, pathlib
d = pathlib.Path(sys.argv[1]); ids = [it["id"] for it in json.load(open(sys.argv[2]))["items"]]
n = 0
for i in ids:
    p = d / f"item-{i}.json"
    if p.exists():
        try:
            r = json.loads(p.read_text())
        except Exception:
            continue
        if all(a in r.get("arms", {}) for a in ("base", "focus")): n += 1
print(n)
PYEOF
}
echo "eval start N=$N t_max=$TMAX ceiling=$CEIL $(date -u +%FT%TZ)" >> $LOG/exp4c-eval.log
final=0
for i in $(seq 1 14); do
  done_n=$(complete); [ "$done_n" -ge "$N" ] && break
  [ -f $D/BUDGET_EXHAUSTED.json ] && { echo "ceiling reached $(date -u +%FT%TZ)" >> $LOG/exp4c-eval.log; break; }
  until ! grep -q '"name":"stencil-' ~/.gb10-gpu.reservations 2>/dev/null; do sleep 30; done
  bash $R/tools/gpu_reserve.sh stencil-exp4c-eval-$i 55 32 -- $PY $R/scripts/memorycode_package_run.py --items-file $F --qualification $Q --resident-limit 3000 >> $LOG/exp4c-eval.log 2>&1
  status=$?
  echo "slice $i exit=$status $(date -u +%FT%TZ) complete=$(complete)/$N" >> $LOG/exp4c-eval.log
  if [ $status -ne 0 ]; then echo "runner failed (exit $status); queue stopped" >> $LOG/exp4c-eval.log; final=$status; break; fi
done
echo "eval queue finished $(date -u +%FT%TZ) complete=$(complete)/$N" >> $LOG/exp4c-eval.log
touch $LOG/exp4c-eval.done
exit $final
