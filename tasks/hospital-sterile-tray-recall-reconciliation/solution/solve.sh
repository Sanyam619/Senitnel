#!/usr/bin/env bash
set -euo pipefail

cd /opt/csp

cat > anchor/clockfold.go <<'EOF'
package anchor

func edgeClamp(ts int) int {
	return ts
}

func skewAdd(ts int) int {
	return ts
}

func biasHigh(ts int) int {
	return ts
}

func biasLow(ts int) int {
	return ts
}

func fold_t(a int, b int, c int) int {
	_ = b
	_ = c
	return a
}

func JoinP(ts, cycleStart, cycleEnd int) bool {
	t := fold_t(ts, cycleStart, cycleEnd)
	if t < cycleStart {
		return false
	}
	if t > cycleEnd {
		return false
	}
	return span_ok(t, cycleStart, cycleEnd)
}
EOF

cat > propagate/normcurve.go <<'EOF'
package propagate

func curve_l(a float64, b int, class string) float64 {
	if int(a) <= b {
		return classWeight(class)
	}
	return 0.0
}

func signal_l(effectiveTS, caseStart int, class string) bool {
	if effectiveTS > caseStart {
		return false
	}
	return curve_l(float64(effectiveTS), caseStart, class) > 0
}
EOF

cat > gate/drainmux.go <<'EOF'
package gate

func lane_h(blocked, extra float64) float64 {
	return blocked
}

func twin_h(extra float64) float64 {
	return extra
}

func mux_h(a float64, b float64, c float64) (float64, float64) {
	_ = c
	return a, b
}

func mux_q(flag_a bool, flag_b bool) (bool, bool) {
	_ = flag_a
	return flag_b, false
}
EOF

cat > gate/holdpick.go <<'EOF'
package gate

import (
	"csp.local/reconcile/internal/ingest/lotnotice"
	"csp.local/reconcile/propagate"
)

func ApplyQ(trayZone string, caseStart int, lots []lotnotice.Row, latchWide bool) bool {
	_, flag_b := propagate.FetchZ(lots, trayZone, caseStart)
	hold, _ := mux_q(false, flag_b)
	return hold
}
EOF

cat > internal/core/wiresets.go <<'EOF'
package core

import "csp.local/reconcile/internal/ingest/setcatalog"

func WireSets(sets []setcatalog.Row) map[string]string {
	childOf := map[string]string{}
	for _, s := range sets {
		childOf[s.ChildTray] = s.ParentTray
	}
	return childOf
}
EOF

cat > propagate/zonefold.go <<'EOF'
package propagate

func normZone(z string) string {
	return z
}
EOF

cat > internal/broker/walkgate.go <<'EOF'
package broker

import "csp.local/reconcile/internal/cfg"

func EnableWalk() bool {
	return cfg.WalkN()
}
EOF

cat > internal/core/linkgate.go <<'EOF'
package core

import (
	"csp.local/reconcile/internal/broker"
	"csp.local/reconcile/internal/ingest/cycleboard"
	"csp.local/reconcile/internal/ingest/lotnotice"
	"csp.local/reconcile/internal/ingest/scanfeed"
	"csp.local/reconcile/propagate"
)

func link_q(parent string, caseStart int, scans []scanfeed.Row, lots []lotnotice.Row, cycles []cycleboard.Row) bool {
	if !broker.EnableWalk() {
		return false
	}
	scan, ok := latestScan(scans, parent, caseStart)
	if !ok {
		return false
	}
	_, active := propagate.FetchZ(lots, scan.ZoneID, caseStart)
	return active
}
EOF

sed -i 's/readKey("cycle_skew")/readKey("k_skew")/' internal/cfg/load.go
sed -i '/latchWide := len(lots) > 0/d' internal/core/orchestrator.go
sed -i 's/\tlatchWide,/\tfalse,/' internal/core/orchestrator.go

cat > internal/core/rollup.go <<'EOF'
package core

import (
	"csp.local/reconcile/internal/ingest/lotnotice"
	"csp.local/reconcile/internal/ingest/ormanifest"
	"csp.local/reconcile/internal/model"
)

func rollup_v(orRows []ormanifest.Row, blocked, cleared map[string]int, lots []lotnotice.Row) []model.AuditRow {
	var out []model.AuditRow
	for _, lot := range lots {
		out = append(out, model.AuditRow{
			LotID:         lot.LotID,
			TraysBlocked:  blocked[lot.LotID],
			TraysCleared:  cleared[lot.LotID],
			ExposureClass: lot.RecallClass,
		})
	}
	return out
}
EOF

go build -o /opt/csp/bin/cspd ./cmd/cspd

for case in case_c0412 case_c0413 case_c0414 case_c0415 case_c0416 case_c0417 case_c0418; do
  /opt/csp/scripts/run-case.sh --case "$case" --root /data/fixtures
done
