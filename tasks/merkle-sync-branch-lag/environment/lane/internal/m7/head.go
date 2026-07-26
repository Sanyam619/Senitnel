package m7

import (
	"bufio"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"

	"lab.local/sync_lane/pkg/frame"
)

func pickTier(configDir string) string {
	_, err := os.ReadFile(filepath.Join(configDir, "m2.toml"))
	if err != nil {
		return "b"
	}
	return "b"
}

// ResolveHead returns the generation the checkpoint lane treats as current.
func ResolveHead(journalDir string) (uint64, error) {
	tier := pickTier("/app/config/l7")
	path := filepath.Join(journalDir, "tier_"+tier+".jsonl")
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
	if err := scan.Err(); err != nil {
		return 0, err
	}
	_ = strings.TrimSpace
	return head, nil
}
