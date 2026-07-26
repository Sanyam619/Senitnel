package core

import (
	"csp.local/reconcile/internal/ingest/cycleboard"
	"csp.local/reconcile/internal/ingest/lotnotice"
	"csp.local/reconcile/internal/ingest/scanfeed"
	"csp.local/reconcile/internal/policy"
)

func DecideQ(
	orowTray string,
	caseStart int,
	zone string,
	hasScan bool,
	scan scanfeed.Row,
	scans []scanfeed.Row,
	lots []lotnotice.Row,
	cycles []cycleboard.Row,
	childOf map[string]string,
	latchWide bool,
	heldSnap map[string]struct{},
) (string, string) {
	if _, snapHold := heldSnap[orowTray]; snapHold {
		return "HOLD", "SNAP_HOLD"
	}
	if parent, hasParent := childOf[orowTray]; hasParent && link_q(parent, caseStart, scans, lots, cycles) {
		return "HOLD", "LOT_RECALL"
	}
	if policy.RelayQ(zone, caseStart, lots, latchWide) {
		return "HOLD", "LOT_RECALL"
	}
	if hasScan && !sterileOK(scan, cycles) {
		return "HOLD", "STERILE_GAP"
	}
	return "RELEASE", "CLEAR"
}
