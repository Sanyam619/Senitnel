#!/usr/bin/env bash
set -euo pipefail
cd /app

export PATH="/app/bin:/usr/local/go/bin:${PATH:-}"

runtime=/app/data/state/runtime.json
fleet=/app/config/profiles/fleet.toml
notes=/app/ops/mesh-notes.toml
epoch=$(grep -o '"epoch"[[:space:]]*:[[:space:]]*[0-9]*' "$runtime" | head -1 | grep -o '[0-9]*$')
target=$(grep -o 'target_root[[:space:]]*=[[:space:]]*"[^"]*"' "$fleet" | head -1 | cut -d'"' -f2)
echo "epoch=$epoch target=$target"

cat > /app/lane/fold_a.go <<'EOF'
package lane

import (
	"bytes"
	"fmt"
	"os"
	"os/exec"
)

// fold_a is the issuance publish driver entry.
func fold_a() error {
	cmd := exec.Command("/app/bin/meshctl", "bundlepub")
	var stderr bytes.Buffer
	cmd.Stderr = &stderr
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("bundlepub: %w (%s)", err, stderr.String())
	}
	live := "/app/data/state/live-bundle.json"
	raw, err := os.ReadFile(live)
	if err != nil {
		return err
	}
	if !bytes.Contains(raw, []byte(`"active_root"`)) {
		return fmt.Errorf("live bundle missing active_root")
	}
	if !bytes.Contains(raw, []byte(`"generation"`)) {
		return fmt.Errorf("live bundle missing generation")
	}
	if !bytes.Contains(raw, []byte(`"kid"`)) {
		return fmt.Errorf("live bundle missing kid")
	}
	if !bytes.Contains(raw, []byte(`"epoch"`)) {
		return fmt.Errorf("live bundle missing epoch")
	}
	return nil
}
EOF

cat > /app/seat/sieve_b.go <<'EOF'
package seat

import (
	"bytes"
	"fmt"
	"os"
	"os/exec"
)

// sieve_b is the TrustManager rebind driver entry.
func sieve_b() error {
	cmd := exec.Command("/app/bin/meshctl", "tmrebind")
	var stderr bytes.Buffer
	cmd.Stderr = &stderr
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("tmrebind: %w (%s)", err, stderr.String())
	}
	raw, err := os.ReadFile("/app/data/state/tm-cache.json")
	if err != nil {
		return err
	}
	if !bytes.Contains(raw, []byte(`"warm": false`)) && !bytes.Contains(raw, []byte(`"warm":false`)) {
		return fmt.Errorf("cache still warm")
	}
	if !bytes.Contains(raw, []byte(`"last_root"`)) {
		return fmt.Errorf("cache missing last_root")
	}
	if !bytes.Contains(raw, []byte(`"last_epoch"`)) {
		return fmt.Errorf("cache missing last_epoch")
	}
	return nil
}
EOF

cat > /app/roll/emit_c.go <<'EOF'
package roll

import (
	"bytes"
	"fmt"
	"os"
	"os/exec"
)

// emit_c is the ticket-floor driver entry.
func emit_c() error {
	cmd := exec.Command("/app/bin/meshctl", "tickgate")
	var stderr bytes.Buffer
	cmd.Stderr = &stderr
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("tickgate: %w (%s)", err, stderr.String())
	}
	raw, err := os.ReadFile("/app/data/state/ticket-gate.json")
	if err != nil {
		return err
	}
	if !bytes.Contains(raw, []byte(`"min_ticket_epoch"`)) {
		return fmt.Errorf("ticket gate missing min_ticket_epoch")
	}
	if bytes.Contains(raw, []byte(`"min_ticket_epoch":0`)) || bytes.Contains(raw, []byte(`"min_ticket_epoch": 0`)) {
		return fmt.Errorf("ticket floor still zero")
	}
	return nil
}
EOF

echo "== run cutover drivers =="
/app/bin/meshctl cutover

live=/app/data/state/live-bundle.json
grep -q "$target" "$live"
cache=/app/data/state/tm-cache.json
grep -Eq '"warm":[[:space:]]*false' "$cache"
gate=/app/data/state/ticket-gate.json
grep -q "$epoch" "$gate"

echo "== probe =="
/app/bin/readycheck >/dev/null || true
/app/bin/meshctl probe
test -f /output/mesh-cutover.json
note_cases=$(grep -c '^\[cases\.' "$notes")
test "$note_cases" -ge 6
echo "oracle cutover complete"
