package k3

import (
	"bufio"
	"encoding/json"
	"os"
	"path/filepath"

	"lab.local/sync_lane/pkg/frame"
)

// ScanTierA walks tier_a for a standalone anchor helper not wired into emit.
func ScanTierA(journalDir string) (uint64, error) {
	path := filepath.Join(journalDir, "tier_a.jsonl")
	f, err := os.Open(path)
	if err != nil {
		return 0, err
	}
	defer f.Close()

	var head uint64
	scan := bufio.NewScanner(f)
	for scan.Scan() {
		line := scan.Text()
		if line == "" {
			continue
		}
		var row frame.JournalRow
		if err := json.Unmarshal([]byte(line), &row); err != nil {
			return 0, err
		}
		if row.Gen > head {
			head = row.Gen
		}
	}
	return head, scan.Err()
}
