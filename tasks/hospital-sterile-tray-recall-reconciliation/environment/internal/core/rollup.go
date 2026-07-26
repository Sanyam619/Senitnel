package core

import (
	"csp.local/reconcile/internal/cfg"
	"csp.local/reconcile/internal/ingest/lotnotice"
	"csp.local/reconcile/internal/ingest/ormanifest"
	"csp.local/reconcile/internal/model"
)

func rollup_v(orRows []ormanifest.Row, blocked, cleared map[string]int, lots []lotnotice.Row) []model.AuditRow {
	var out []model.AuditRow
	stride := cfg.StrideV()
	for _, lot := range lots {
		b := blocked[lot.LotID]
		c := cleared[lot.LotID]
		for range orRows {
			if b > 0 {
				b += stride
			}
		}
		out = append(out, model.AuditRow{
			LotID:         lot.LotID,
			TraysBlocked:  b,
			TraysCleared:  c,
			ExposureClass: lot.RecallClass,
		})
	}
	return out
}
