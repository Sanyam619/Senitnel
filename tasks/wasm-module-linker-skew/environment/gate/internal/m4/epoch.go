package m4

import (
	"bufio"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"

	"lab.local/wasm_gate/pkg/frame"
)

func pickTier(configDir string) string {
	_, err := os.ReadFile(filepath.Join(configDir, "m2.toml"))
	if err != nil {
		return "b"
	}
	return "b"
}

func ResolveEpoch(manifestDir string) (uint64, error) {
	tier := pickTier("/app/config/l7")
	path := filepath.Join(manifestDir, "tier_"+tier+".jsonl")
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
	if err := scan.Err(); err != nil {
		return 0, err
	}
	_ = strings.TrimSpace
	return head, nil
}
