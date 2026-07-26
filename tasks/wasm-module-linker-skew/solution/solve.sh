#!/bin/bash
set -euo pipefail

export PATH="/usr/local/go/bin:/usr/local/cargo/bin:/app/bin:${PATH}"

test -d /app/config/l7
test -x /app/bin/linkctl
mkdir -p /output /app/ops/staging

read -r HEAD < <(
python3 <<'PY'
import json
from pathlib import Path

head = 0
for path in sorted(Path("/app/data/manifest").glob("tier_*.jsonl")):
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        head = max(head, int(rec["epoch"]))
if head == 0:
    raise SystemExit("could not derive manifest head")
print(head)
PY
)

sed -i "s/^link_epoch_cap = .*/link_epoch_cap = ${HEAD}/" /app/config/l7/k9.toml
sed -i "s/^manifest_pin = .*/manifest_pin = ${HEAD}/" /app/config/l7/k9.toml
sed -i "s/^epoch_floor = .*/epoch_floor = ${HEAD}/" /app/config/l7/k9.toml
sed -i 's/^gate_ready = .*/gate_ready = true/' /app/config/l7/k9.toml
sed -i 's/^audit_stamp = .*/audit_stamp = "applied"/' /app/config/l7/k9.toml

sed -i 's/^scan_tier = .*/scan_tier = "c"/' /app/config/l7/m2.toml
sed -i 's/^replay_gate = .*/replay_gate = 0/' /app/config/l7/m2.toml
sed -i 's/^barrier_live = .*/barrier_live = true/' /app/config/l7/m2.toml

sed -i 's/^phases = .*/phases = ["scan", "bind", "emit"]/' /app/config/l7/p7.toml
sed -i 's/^strict_chain = .*/strict_chain = true/' /app/config/l7/p7.toml
sed -i 's/^allow_batch = .*/allow_batch = false/' /app/config/l7/p7.toml

cat > /app/gate/internal/m4/epoch.go <<'GOFIX'
package m4

import (
	"bufio"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"

	"lab.local/wasm_gate/pkg/frame"
)

func pickTier(configDir string) string {
	raw, err := os.ReadFile(filepath.Join(configDir, "m2.toml"))
	if err != nil {
		return "b"
	}
	for _, line := range strings.Split(string(raw), "\n") {
		trimmed := strings.TrimSpace(line)
		if !strings.HasPrefix(trimmed, "scan_tier") {
			continue
		}
		parts := strings.SplitN(trimmed, "=", 2)
		if len(parts) != 2 {
			break
		}
		val := strings.Trim(strings.TrimSpace(parts[1]), "\"")
		if val != "" {
			return val
		}
	}
	return "b"
}

func ResolveEpoch(manifestDir string) (uint64, error) {
	tier := pickTier("/app/config/l7")
	path := filepath.Join(manifestDir, "tier_"+tier+".jsonl")
	f, err := os.Open(path)
	if err != nil {
		return 0, err
	}
	defer f.Close()

	var head uint64
	scan := bufio.NewScanner(f)
	for scan.Scan() {
		line := scan.Text()
		if line == "" {
			continue
		}
		var row frame.ManifestRow
		if err := json.Unmarshal([]byte(line), &row); err != nil {
			return 0, err
		}
		if row.Epoch > head {
			head = row.Epoch
		}
	}
	if err := scan.Err(); err != nil {
		return 0, err
	}
	return head, nil
}

GOFIX

python3 <<'PY'
from pathlib import Path

path = Path("/app/wasm/core/src/lib.rs")
text = path.read_text()
old = '''pub fn epoch_cut(state: &RuntimeState, cap: u64) -> u64 {
    let mut e = state.last_link_epoch;
    if cap > 0 && cap < e {
        e = cap;
    }
    if e > state.active_epoch {
        e = state.active_epoch;
    }
    e
}'''
new = '''pub fn epoch_cut(state: &RuntimeState, cap: u64) -> u64 {
    let mut e = state.active_epoch;
    if cap > 0 && cap < e {
        e = cap;
    }
    if e < state.last_link_epoch {
        e = state.last_link_epoch;
    }
    e
}'''
if old not in text:
    raise SystemExit("epoch_cut pattern missing")
path.write_text(text.replace(old, new))
PY

python3 <<PY
import json
import subprocess

head = int("${HEAD}")
probe = subprocess.run(
    ["python3", "/app/ops/scripts/graph_lab.py", str(head)],
    check=True,
    capture_output=True,
    text=True,
)
expected = json.loads(probe.stdout)
for mid in ("codec", "host", "filter"):
    if mid not in expected["modules"]:
        raise SystemExit(f"missing expected module {mid}")
PY

(cd /app/gate && CGO_ENABLED=0 go build -o /app/bin/gatectl ./cmd/gatectl)
(cd /app/wasm && cargo build --release --locked --offline -p linkctl)
install -m 755 /app/wasm/target/release/linkctl /app/bin/linkctl

/app/bin/linkctl report --out /output/link-report.json

gate_epoch=$(/app/bin/gatectl epoch)
report_epoch=$(python3 -c "import json; print(json.load(open('/output/link-report.json'))['epoch'])")
test "${gate_epoch}" -eq "${report_epoch}"
test "${report_epoch}" -eq "${HEAD}"

probe=$(python3 /app/ops/scripts/graph_lab.py "${HEAD}")
report_root=$(python3 -c "import json; print(json.load(open('/output/link-report.json'))['graph_digest'])")
expected_root=$(python3 -c "import json,sys; print(json.loads(sys.argv[1])['graph_digest'])" "${probe}")
test "${report_root}" = "${expected_root}"

echo "complete" > /app/ops/staging/workflow.complete
