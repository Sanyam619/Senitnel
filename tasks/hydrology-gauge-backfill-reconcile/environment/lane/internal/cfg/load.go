package cfg

import (
	"os"
	"path/filepath"
	"strconv"
	"strings"
)

func readTable(configDir, table string) map[string]string {
	out := map[string]string{}
	raw, err := os.ReadFile(filepath.Join(configDir, table))
	if err != nil {
		return out
	}
	for _, line := range strings.Split(string(raw), "\n") {
		trimmed := strings.TrimSpace(line)
		if trimmed == "" || strings.HasPrefix(trimmed, "#") {
			continue
		}
		parts := strings.SplitN(trimmed, "=", 2)
		if len(parts) != 2 {
			continue
		}
		key := strings.TrimSpace(parts[0])
		val := strings.TrimSpace(parts[1])
		out[key] = val
	}
	return out
}

func ScanTier(configDir string) string {
	tbl := readTable(configDir, "m2.toml")
	if raw, ok := tbl["scan_tier"]; ok {
		return strings.Trim(raw, "\"")
	}
	return "b"
}

func JournalPin(configDir string) (uint64, bool) {
	tbl := readTable(configDir, "k9.toml")
	raw, ok := tbl["journal_pin"]
	if !ok {
		return 0, false
	}
	val, err := strconv.ParseUint(raw, 10, 64)
	if err != nil {
		return 0, false
	}
	return val, true
}

func RollReady(configDir string) bool {
	tbl := readTable(configDir, "k9.toml")
	return strings.TrimSpace(tbl["roll_ready"]) == "true"
}
