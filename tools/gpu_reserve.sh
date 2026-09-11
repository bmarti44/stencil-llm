#!/usr/bin/env bash
# Shared-GPU reservation wrapper (plan/BACK-ON-TRACK-PLAN.md section E, 2026-09-11).
# usage: tools/gpu_reserve.sh <name> <est-minutes> <peak-gb> [--exclusive] -- <cmd...>
# Appends {"name","pid","started","eta_min","peak_gb"} to ~/.gb10-gpu.reservations under
# flock, registers the pid in .stencil-owned-pids, refuses to launch when free memory is
# below own peak + sum of other reservations' peaks + headroom, removes its line on exit.
set -euo pipefail
RES="${GB10_RESERVATIONS:-$HOME/.gb10-gpu.reservations}"
LOCK="${GB10_LOCK:-$HOME/.gb10-gpu.lock}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HEADROOM_GB="${GB10_HEADROOM_GB:-8}"
if [ $# -lt 5 ]; then
  echo "usage: $0 <name> <est-minutes> <peak-gb> [--exclusive] -- <cmd...>" >&2
  exit 2
fi
name="$1"; eta="$2"; peak="$3"; shift 3
exclusive=0
if [ "${1:-}" = "--exclusive" ]; then exclusive=1; shift; fi
[ "${1:-}" = "--" ] && shift
[ $# -gt 0 ] || { echo "gpu_reserve: no command given" >&2; exit 2; }
touch "$RES"
others=$(python3 - "$RES" <<'PY'
import json, sys
total = 0.0
for line in open(sys.argv[1]):
    line = line.strip()
    if not line:
        continue
    try:
        total += float(json.loads(line).get("peak_gb", 0))
    except Exception:
        pass
print(total)
PY
)
free_gb=$(free -g | awk '/^Mem:/ {print $7}')
if python3 -c "import sys; sys.exit(0 if $free_gb < $peak + $others + $HEADROOM_GB else 1)"; then
  echo "gpu_reserve: refusing $name: free ${free_gb} GB < own $peak + others $others + headroom $HEADROOM_GB GB" >&2
  exit 3
fi
if [ "$exclusive" = 1 ]; then
  exec 9>"$LOCK"
  flock -n 9 || { echo "gpu_reserve: exclusive lock held" >&2; exit 4; }
fi
"$@" &
pid=$!
stamp=$(date -u +%FT%TZ)
line=$(printf '{"name":"%s","pid":%d,"started":"%s","eta_min":%s,"peak_gb":%s}' "$name" "$pid" "$stamp" "$eta" "$peak")
( flock 8; echo "$line" >> "$RES" ) 8>"$RES.lock"
echo "$pid" >> "$ROOT/.stencil-owned-pids"
cleanup() {
  ( flock 8; grep -v "\"pid\":$pid," "$RES" > "$RES.tmp" || true; mv "$RES.tmp" "$RES" ) 8>"$RES.lock"
}
trap cleanup EXIT
wait "$pid"
