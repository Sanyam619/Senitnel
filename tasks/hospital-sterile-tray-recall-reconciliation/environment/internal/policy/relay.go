package policy

import (
	"csp.local/reconcile/gate"
	"csp.local/reconcile/internal/ingest/lotnotice"
)

func RelayQ(trayZone string, caseStart int, lots []lotnotice.Row, latchWide bool) bool {
	return gate.ApplyQ(trayZone, caseStart, lots, latchWide)
}
