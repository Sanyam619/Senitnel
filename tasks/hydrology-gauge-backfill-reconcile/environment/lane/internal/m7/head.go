package m7

import (
	"bufio"
	"encoding/json"
	"os"
	"path/filepath"

	"lab.local/hydro_lane/internal/cfg"
	"lab.local/hydro_lane/pkg/frame"
)

func ResolveHead(journalDir, configDir string) (uint64, error) {
	tier := cfg.ScanTier(configDir)
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
	if !cfg.RollReady(configDir) {
		if pin, ok := cfg.JournalPin(configDir); ok && pin < head {
			head = pin
		}
	}
	return head, nil
}
