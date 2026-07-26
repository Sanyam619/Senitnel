package lane

import (
	"os"
	"path/filepath"
)

// fold_a is the issuance publish driver entry.
func fold_a() error {
	side := "/app/data/state/side"
	if err := os.MkdirAll(side, 0o755); err != nil {
		return err
	}
	src := "/app/data/material/ca-side.pem"
	dst := filepath.Join(side, "ca-side.pem")
	raw, err := os.ReadFile(src)
	if err != nil {
		return err
	}
	return os.WriteFile(dst, raw, 0o644)
}
