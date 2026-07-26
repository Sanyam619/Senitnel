#!/bin/bash
set -euo pipefail

export PATH="/usr/local/go/bin:/usr/local/cargo/bin:/app/bin:${PATH}"

test -d /app/config/l7
test -x /app/bin/syncctl
mkdir -p /output /app/ops/staging

read -r HEAD < <(
python3 <<'PY'
import json
from pathlib import Path

head = 0
for path in sorted(Path("/app/data/journal").glob("tier_*.jsonl")):
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        head = max(head, int(rec["gen"]))
if head == 0:
    raise SystemExit("could not derive journal head")
print(head)
PY
)

sed -i "s/^branch_cap = .*/branch_cap = ${HEAD}/" /app/config/l7/k9.toml
sed -i "s/^journal_pin = .*/journal_pin = ${HEAD}/" /app/config/l7/k9.toml
sed -i "s/^head_floor = .*/head_floor = ${HEAD}/" /app/config/l7/k9.toml
sed -i 's/^sync_ready = .*/sync_ready = true/' /app/config/l7/k9.toml
sed -i 's/^audit_stamp = .*/audit_stamp = "applied"/' /app/config/l7/k9.toml

sed -i 's/^scan_tier = .*/scan_tier = "c"/' /app/config/l7/m2.toml
sed -i 's/^replay_gate = .*/replay_gate = 0/' /app/config/l7/m2.toml
sed -i 's/^barrier_live = .*/barrier_live = true/' /app/config/l7/m2.toml

sed -i 's/^phases = .*/phases = ["scan", "bind", "emit"]/' /app/config/l7/p7.toml
sed -i 's/^strict_chain = .*/strict_chain = true/' /app/config/l7/p7.toml
sed -i 's/^allow_batch = .*/allow_batch = false/' /app/config/l7/p7.toml

cat > /app/lane/internal/m7/head.go <<'GOFIX'
package m7

import (
	"bufio"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"

	"lab.local/sync_lane/pkg/frame"
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

func ResolveHead(journalDir string) (uint64, error) {
	tier := pickTier("/app/config/l7")
	path := filepath.Join(journalDir, "tier_"+tier+".jsonl")
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
		var row frame.JournalRow
		if err := json.Unmarshal([]byte(line), &row); err != nil {
			return 0, err
		}
		if row.Gen > head {
			head = row.Gen
		}
	}
	if err := scan.Err(); err != nil {
		return 0, err
	}
	return head, nil
}

GOFIX

cat > /app/lane/internal/m7/summary.go <<'GOFIX'
package m7

import (
	"encoding/json"
	"os"
	"path/filepath"

	"lab.local/sync_lane/pkg/frame"
)

func WriteSummary(outPath, dataRoot string) error {
	gen, err := ResolveHead(filepath.Join(dataRoot, "journal"))
	if err != nil {
		return err
	}
	root, leaves, err := readTreeSnapshot(dataRoot, gen)
	if err != nil {
		return err
	}
	doc := frame.SummaryDoc{
		BranchGen:  gen,
		RootDigest: root,
		Leaves:     leaves,
	}
	payload, err := json.MarshalIndent(doc, "", "  ")
	if err != nil {
		return err
	}
	payload = append(payload, '\n')
	if err := os.MkdirAll(filepath.Dir(outPath), 0o755); err != nil {
		return err
	}
	return os.WriteFile(outPath, payload, 0o644)
}

func readTreeSnapshot(dataRoot string, gen uint64) (string, map[string]string, error) {
	return buildAt(dataRoot, gen)
}

GOFIX

python3 <<'PY'
from pathlib import Path

path = Path("/app/tree/core/src/lib.rs")
text = path.read_text()
old = '''pub fn branch_cut(state: &RuntimeState, cap: u64) -> u64 {
    let mut g = state.last_sync_gen;
    if cap > 0 && cap < g {
        g = cap;
    }
    if g > state.active_gen {
        g = state.active_gen;
    }
    g
}'''
new = '''pub fn branch_cut(state: &RuntimeState, cap: u64) -> u64 {
    let mut g = state.active_gen;
    if cap > 0 && cap < g {
        g = cap;
    }
    if g < state.last_sync_gen {
        g = state.last_sync_gen;
    }
    g
}'''
if old not in text:
    raise SystemExit("branch_cut pattern missing")
path.write_text(text.replace(old, new))
PY

python3 <<PY
import json
import subprocess

head = int("${HEAD}")
probe = subprocess.run(
    ["python3", "/app/ops/scripts/digest_lab.py", str(head)],
    check=True,
    capture_output=True,
    text=True,
)
expected = json.loads(probe.stdout)
for leaf in ("alpha", "gamma", "delta"):
    if leaf not in expected["leaves"]:
        raise SystemExit(f"missing expected leaf {leaf}")
PY

(cd /app/lane && CGO_ENABLED=0 go build -o /app/bin/lane ./cmd/lane)
(cd /app/tree && cargo build --release --locked --offline -p syncctl)
install -m 755 /app/tree/target/release/syncctl /app/bin/syncctl

/app/bin/syncctl report --out /output/sync-report.json

lane_head=$(/app/bin/lane head)
report_gen=$(python3 -c "import json; print(json.load(open('/output/sync-report.json'))['branch_gen'])")
test "${lane_head}" -eq "${report_gen}"
test "${report_gen}" -eq "${HEAD}"

probe=$(python3 /app/ops/scripts/digest_lab.py "${HEAD}")
report_root=$(python3 -c "import json; print(json.load(open('/output/sync-report.json'))['root_digest'])")
expected_root=$(python3 -c "import json,sys; print(json.loads(sys.argv[1])['root_digest'])" "${probe}")
test "${report_root}" = "${expected_root}"

echo "complete" > /app/ops/staging/workflow.complete
