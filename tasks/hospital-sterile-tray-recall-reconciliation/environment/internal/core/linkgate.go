package core

import (
	"csp.local/reconcile/internal/broker"
	"csp.local/reconcile/internal/ingest/cycleboard"
	"csp.local/reconcile/internal/ingest/lotnotice"
	"csp.local/reconcile/internal/ingest/scanfeed"
)

func link_q(parent string, caseStart int, scans []scanfeed.Row, lots []lotnotice.Row, cycles []cycleboard.Row) bool {
	if !broker.EnableWalk() {
		return false
	}
	_ = parent
	_ = caseStart
	_ = scans
	_ = lots
	_ = cycles
	return false
}
