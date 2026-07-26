package core

import (
	"csp.local/reconcile/internal/ingest/cycleboard"
	"csp.local/reconcile/internal/ingest/lotnotice"
	"csp.local/reconcile/internal/ingest/ormanifest"
	"csp.local/reconcile/internal/ingest/quarantinesnap"
	"csp.local/reconcile/internal/ingest/scanfeed"
	"csp.local/reconcile/internal/ingest/setcatalog"
)

type CaseCtx struct {
	CaseName string
	Root     string
	Scans    []scanfeed.Row
	Cycles   []cycleboard.Row
	Lots     []lotnotice.Row
	ORRows   []ormanifest.Row
	Sets     []setcatalog.Row
	Snap     quarantinesnap.Doc
}
