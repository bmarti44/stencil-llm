#!/usr/bin/env bash
set -eu

repo_root="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
manifest="$repo_root/data/bench/pins-manifest.json"
sealed="$repo_root/data/bench/ifeval_input_data.jsonl"

expected="$(python3 -c 'import json, sys; print(json.load(open(sys.argv[1]))["sealed_sha256"])' "$manifest")"
actual="$(sha256sum "$sealed" | awk '{print $1}')"
if [ "$actual" != "$expected" ]; then
    echo "sealed hash mismatch: expected $expected, got $actual" >&2
    exit 1
fi

# Same-UID accident barrier only; ordinary Git checkouts do not preserve write bits.
chmod 0444 "$sealed"
echo "sealed hash verified; mode set to 0444: $sealed"
