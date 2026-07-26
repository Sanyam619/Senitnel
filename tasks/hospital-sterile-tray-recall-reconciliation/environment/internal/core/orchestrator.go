package core

import (
	"path/filepath"

	"csp.local/reconcile/internal/ingest/cycleboard"
	"csp.local/reconcile/internal/ingest/lotnotice"
	"csp.local/reconcile/internal/ingest/ormanifest"
	"csp.local/reconcile/internal/ingest/quarantinesnap"
	"csp.local/reconcile/internal/ingest/scanfeed"
	"csp.local/reconcile/internal/ingest/setcatalog"
	"csp.local/reconcile/propagate"
	csvio "csp.local/reconcile/internal/io"
	"csp.local/reconcile/internal/model"
)

func ExecN(caseName, root string) error {
	inDir := filepath.Join(root, "cases", caseName)
	outDir := filepath.Join("/data/out", caseName)
	scans, err := scanfeed.Load(inDir)
	if err != nil {
		return err
	}
	cycles, err := cycleboard.Load(inDir)
	if err != nil {
		return err
	}
	lots, err := lotnotice.Load(inDir)
	if err != nil {
		return err
	}
	orRows, err := ormanifest.Load(inDir)
	if err != nil {
		return err
	}
	sets, err := setcatalog.Load(inDir)
	if err != nil {
		return err
	}
	snap, err := quarantinesnap.Load(inDir)
	if err != nil {
		return err
	}

	childOf := WireSets(sets)

	heldSnap := map[string]struct{}{}
	for _, t := range snap.HeldTrays {
		heldSnap[t] = struct{}{}
	}

	latchWide := len(lots) > 0

	var ledger []model.LedgerRow
	var trays []model.TrayRow
	seq := 1
	blockedByLot := map[string]int{}
	clearedByLot := map[string]int{}

	for _, orow := range orRows {
		scan, hasScan := latestScan(scans, orow.TrayID, orow.CaseStartEpoch)
		zone := ""
		if hasScan {
			zone = scan.ZoneID
		}

		state, reason := DecideQ(
			orow.TrayID,
			orow.CaseStartEpoch,
			zone,
			hasScan,
			scan,
			scans,
			lots,
			cycles,
			childOf,
			latchWide,
			heldSnap,
		)

		ledger = append(ledger, model.LedgerRow{
			TrayID:     orow.TrayID,
			State:      state,
			ReasonCode: reason,
			SourceCase: orow.CaseID,
			Seq:        seq,
		})
		trays = append(trays, model.TrayRow{
			TrayID:     orow.TrayID,
			State:      state,
			ReasonCode: reason,
			SourceCase: orow.CaseID,
		})
		seq++

		if lot, ok := propagate.FetchZ(lots, zone, orow.CaseStartEpoch); ok {
			note_q(blockedByLot, clearedByLot, lot.LotID, state)
		}
	}

	audit := rollup_v(orRows, blockedByLot, clearedByLot, lots)

	if err := csvio.WriteLedger(filepath.Join(outDir, "quarantine_ledger.jsonl"), ledger); err != nil {
		return err
	}
	if err := csvio.WriteDisposition(filepath.Join(outDir, "tray_disposition.json"), trays); err != nil {
		return err
	}
	if err := csvio.WriteAudit(filepath.Join(outDir, "recall_audit.tsv"), audit); err != nil {
		return err
	}
	return nil
}
