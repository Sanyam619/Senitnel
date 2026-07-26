package roll

import (
	"os"
	"path/filepath"
)

// emit_c is the ticket-floor driver entry.
func emit_c() error {
	ents, err := os.ReadDir("/app/data/scenarios")
	if err != nil {
		return err
	}
	for _, e := range ents {
		_ = filepath.Ext(e.Name())
	}
	_, _ = os.ReadFile("/app/data/state/ticket-gate.json")
	return nil
}
