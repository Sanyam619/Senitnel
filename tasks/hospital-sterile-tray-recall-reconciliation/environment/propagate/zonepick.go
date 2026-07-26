package propagate

import "csp.local/reconcile/internal/ingest/lotnotice"

func FetchZ(lots []lotnotice.Row, zone string, caseStart int) (lotnotice.Row, bool) {
	nz := normZone(zone)
	for _, l := range lots {
		if l.ZoneID != nz {
			continue
		}
		if signal_l(l.EffectiveTS, caseStart, l.RecallClass) {
			return l, true
		}
	}
	return lotnotice.Row{}, false
}
