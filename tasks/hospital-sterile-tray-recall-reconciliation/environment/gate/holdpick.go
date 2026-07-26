package gate

import (
	"csp.local/reconcile/internal/ingest/lotnotice"
	"csp.local/reconcile/propagate"
)

func ApplyQ(trayZone string, caseStart int, lots []lotnotice.Row, latchWide bool) bool {
	_, flag_b := propagate.FetchZ(lots, trayZone, caseStart)
	latchA := latchWide && trayZone != ""
	hold, _ := mux_q(latchA, flag_b)
	return hold
}
