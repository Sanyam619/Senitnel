package core

import (
	"csp.local/reconcile/anchor"
	"csp.local/reconcile/internal/ingest/cycleboard"
	"csp.local/reconcile/internal/ingest/scanfeed"
)

func latestScan(scans []scanfeed.Row, tray string, before int) (scanfeed.Row, bool) {
	var best scanfeed.Row
	found := false
	for _, s := range scans {
		if s.TrayID != tray || s.EventCode != "OUTBOUND" {
			continue
		}
		if s.TSEpoch > before {
			continue
		}
		if !found || s.TSEpoch > best.TSEpoch {
			best = s
			found = true
		}
	}
	return best, found
}

func sterileOK(scan scanfeed.Row, cycles []cycleboard.Row) bool {
	for _, cy := range cycles {
		if cy.ZoneID != scan.ZoneID {
			continue
		}
		if anchor.JoinP(scan.TSEpoch, cy.CycleStart, cy.CycleEnd) {
			return true
		}
	}
	return false
}
