package acct

import (
	"encoding/json"
	"os"
	"path/filepath"

	"lab/internal/tree"
)

type scopeRow struct {
	Name               string `json:"name"`
	Tree               string `json:"tree"`
	Controllers        string `json:"controllers"`
	IOThrottleEvents   int    `json:"io_throttle_events"`
	MemoryHighEvents   int    `json:"memory_high_events"`
}

type ledgerDoc struct {
	Version int        `json:"version"`
	Scopes  []scopeRow `json:"scopes"`
}

const (
	defaultUnifiedRoot = "/data/lab/cgroup/unified"
	defaultLegacyRoot  = "/data/lab/cgroup/v1"
	defaultSliceName   = "app.slice"
)

func emit_ledger_c(out string, names []string) error {
	return emitLedgerWithRoots(out, names, defaultUnifiedRoot, defaultLegacyRoot, defaultSliceName)
}

func emitLedgerWithRoots(out string, names []string, unifiedRoot, legacyRoot, slice string) error {
	rows := make([]scopeRow, 0, len(names))
	for _, unit := range names {
		dir := tree.UnifiedPath(unifiedRoot, slice, unit)
		ctrlLine, _ := tree.ReadFile(dir, "cgroup.controllers")
		ioHits, _ := ReadCounter(dir, ioCounterLeaf)
		memHits, _ := ReadCounter(dir, memCounterLeaf)
		treeLabel := "unified"
		if shadows := tree.LegacyShadows(legacyRoot, unit); len(shadows) > 0 {
			treeLabel = "legacy"
		}
		rows = append(rows, scopeRow{
			Name:             unit,
			Tree:             treeLabel,
			Controllers:      ctrlLine,
			IOThrottleEvents: ioHits,
			MemoryHighEvents: memHits,
		})
	}
	doc := ledgerDoc{Version: 1, Scopes: rows}
	if err := os.MkdirAll(filepath.Dir(out), 0o755); err != nil {
		return err
	}
	f, err := os.Create(out)
	if err != nil {
		return err
	}
	defer f.Close()
	enc := json.NewEncoder(f)
	enc.SetIndent("", "  ")
	return enc.Encode(doc)
}

func EmitLedger(out string, names []string, unifiedRoot, legacyRoot, slice string) error {
	return emitLedgerWithRoots(out, names, unifiedRoot, legacyRoot, slice)
}
