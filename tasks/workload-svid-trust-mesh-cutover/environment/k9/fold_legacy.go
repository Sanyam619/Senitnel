package k9

import (
	"os"
	"path/filepath"
)

// FoldLegacy copies a CA side file for ops dry-runs without publishing live-bundle epoch.
func FoldLegacy(src string, dstDir string) error {
	raw, err := os.ReadFile(src)
	if err != nil {
		return err
	}
	if err := os.MkdirAll(dstDir, 0o755); err != nil {
		return err
	}
	return os.WriteFile(filepath.Join(dstDir, "ca-side.pem"), raw, 0o644)
}
