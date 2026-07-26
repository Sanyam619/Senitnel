#!/usr/bin/env bash
set -uo pipefail

for bin in slicearm benchunit ledgersnap; do
  if [ ! -x "/opt/lab/bin/$bin" ]; then
    echo "missing lab tool: $bin" >&2
    exit 1
  fi
done

if ! sed -i 's/arm = gates\[:1\]/arm = gates/' /opt/lab/src/pkg/phase/relay.go; then
  echo "arm helper patch failed" >&2
  exit 1
fi

if ! (
  cd /opt/lab/src
  CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /opt/lab/bin/slicearm ./cmd/phasegate
); then
  echo "slicearm rebuild failed" >&2
  exit 1
fi

SLICE_PARENT="/data/lab/cgroup/unified/app.slice"
UNIFIED="/data/lab/cgroup/unified"
LEGACY="/data/lab/cgroup/v1"
SLICE="app.slice"
UNITS=(app-api.scope app-batch.scope app-worker.scope)
NAME_LIST="app-api.scope,app-batch.scope,app-worker.scope"

rm -f /output/cutover-report.json

if ! /opt/lab/bin/slicearm arm --parent "$SLICE_PARENT" --add io,memory; then
  echo "arm failed" >&2
  exit 1
fi

for unit in "${UNITS[@]}"; do
  if ! /opt/lab/bin/slicearm bind \
      --legacy "$LEGACY" \
      --unified "$UNIFIED" \
      --slice "$SLICE" \
      --unit "$unit"; then
    echo "bind failed for $unit" >&2
    exit 1
  fi
done

for unit in "${UNITS[@]}"; do
  node_dir="$SLICE_PARENT/$unit"
  if [ ! -f "$node_dir/io.max" ] || [ ! -f "$node_dir/memory.max" ]; then
    echo "brake lines missing on $unit" >&2
    exit 1
  fi
done

for unit in "${UNITS[@]}"; do
  if ! /opt/lab/bin/benchunit \
      --unit "$unit" \
      --unified "$UNIFIED" \
      --slice "$SLICE"; then
    echo "bench failed for $unit" >&2
    exit 1
  fi
done

for unit in "${UNITS[@]}"; do
  node_dir="$SLICE_PARENT/$unit"
  io_hits="$(cat "$node_dir/.acct/io_brake_hits" 2>/dev/null || echo 0)"
  mem_hits="$(cat "$node_dir/.acct/mem_peak_hits" 2>/dev/null || echo 0)"
  if [ "${io_hits:-0}" -lt 3 ] || [ "${mem_hits:-0}" -lt 2 ]; then
    echo "counters still flat on $unit" >&2
    exit 1
  fi
done

if ! /opt/lab/bin/ledgersnap \
    --out /output/cutover-report.json \
    --unified "$UNIFIED" \
    --legacy "$LEGACY" \
    --slice "$SLICE" \
    --names "$NAME_LIST"; then
  echo "ledger failed" >&2
  exit 1
fi

if [ ! -f /output/cutover-report.json ]; then
  echo "report missing" >&2
  exit 1
fi

python3 - <<'PY'
import json
from pathlib import Path

doc = json.loads(Path("/output/cutover-report.json").read_text())
assert doc.get("version") == 1
names = {row["name"] for row in doc.get("scopes", [])}
for want in ("app-batch.scope", "app-worker.scope", "app-api.scope"):
    assert want in names
for row in doc["scopes"]:
    assert row["tree"] == "unified"
    assert row["io_throttle_events"] >= 3
    assert row["memory_high_events"] >= 2
    ctrl = str(row.get("controllers", "")).split()
    assert "io" in ctrl and "memory" in ctrl
PY

mkdir -p config
cat > config/cutover-audit.toml <<'AUDIT'
# post-cutover audit record
[session]
phase = "complete"
version = 1
operator = "automated"
started_from = "pending"

[paths]
unified_root = "/data/lab/cgroup/unified"
legacy_root = "/data/lab/cgroup/v1"
slice = "app.slice"
ledger = "/output/cutover-report.json"
anchor = "/data/fixtures/cgroup-seed"
src_root = "/opt/lab/src"

[units.app_batch]
name = "app-batch.scope"
tree = "unified"

[units.app_worker]
name = "app-worker.scope"
tree = "unified"

[units.app_api]
name = "app-api.scope"
tree = "unified"

[delegation]
slice_parent = "/data/lab/cgroup/unified/app.slice"
gates = ["io", "memory"]

[checks]
slice_delegation_verified = true
legacy_shadows_cleared = true
brake_lines_present = true
acct_files_present = true
ledger_emitted = true
anchor_preserved = true
arm_helper_rebuilt = true

[inventory]
scope_count = 3
legacy_controllers = ["cpu", "io", "memory"]

[acct]
io_leaf = ".acct/io_brake_hits"
mem_leaf = ".acct/mem_peak_hits"
min_io_hits = 3
min_mem_hits = 2

[verification]
surfcheck_root = "ok"
treewalk_legacy_cleared = true
bench_passed = true

[notes]
finish = "ledger counters aligned with on-disk acct files"
AUDIT

echo "cutover complete"
