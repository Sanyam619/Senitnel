package k3

import (
	"bufio"
	"encoding/json"
	"os"
	"path/filepath"

	"lab.local/wasm_gate/pkg/frame"
)

func ScanTierA(manifestDir string) (uint64, error) {
	path := filepath.Join(manifestDir, "tier_a.jsonl")
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
		var row frame.ManifestRow
		if err := json.Unmarshal([]byte(line), &row); err != nil {
			return 0, err
		}
		if row.Epoch > head {
			head = row.Epoch
		}
	}
	return head, scan.Err()
}
