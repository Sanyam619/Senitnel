package m4

import (
	"bufio"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"lab.local/pkg_scan/pkg/frame"
)

func readBool(configDir, key string, fallback bool) bool {
	raw, err := os.ReadFile(filepath.Join(configDir, "k9.toml"))
	if err != nil {
		return fallback
	}
	for _, line := range strings.Split(string(raw), "\n") {
		trimmed := strings.TrimSpace(line)
		if !strings.HasPrefix(trimmed, key) {
			continue
		}
		parts := strings.SplitN(trimmed, "=", 2)
		if len(parts) != 2 {
			break
		}
		val := strings.TrimSpace(parts[1])
		return val == "true"
	}
	return fallback
}

func readString(configDir, key, fallback string) string {
	raw, err := os.ReadFile(filepath.Join(configDir, "k9.toml"))
	if err != nil {
		return fallback
	}
	for _, line := range strings.Split(string(raw), "\n") {
		trimmed := strings.TrimSpace(line)
		if !strings.HasPrefix(trimmed, key) {
			continue
		}
		parts := strings.SplitN(trimmed, "=", 2)
		if len(parts) != 2 {
			break
		}
		return strings.Trim(strings.TrimSpace(parts[1]), "\"")
	}
	return fallback
}

func ResolveHead(snapshotDir string) (uint64, error) {
	var head uint64
	for _, name := range []string{"tier_a.jsonl", "tier_b.jsonl", "tier_c.jsonl"} {
		path := filepath.Join(snapshotDir, name)
		f, err := os.Open(path)
		if err != nil {
			continue
		}
		scan := bufio.NewScanner(f)
		for scan.Scan() {
			line := scan.Text()
			if line == "" {
				continue
			}
			var row frame.SnapshotRow
			if err := json.Unmarshal([]byte(line), &row); err != nil {
				f.Close()
				return 0, err
			}
			if row.Gen > head {
				head = row.Gen
			}
		}
		f.Close()
	}
	return head, nil
}

func sevRank(s string) int {
	switch s {
	case "critical":
		return 4
	case "high":
		return 3
	case "medium":
		return 2
	case "low":
		return 1
	default:
		return 0
	}
}

func yankActive(w frame.YankWindow, gen uint64, halfOpen bool, revokes map[string]uint64, honor bool) bool {
	if w.From > gen {
		return false
	}
	key := w.Crate + "@" + w.Vers
	if honor {
		if at, ok := revokes[key]; ok && at <= gen {
			return false
		}
	}
	if w.Until == nil {
		return true
	}
	if halfOpen {
		return gen < *w.Until
	}
	return gen <= *w.Until
}

func loadWindows(path string) ([]frame.YankWindow, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	var out []frame.YankWindow
	scan := bufio.NewScanner(f)
	for scan.Scan() {
		line := scan.Text()
		if line == "" {
			continue
		}
		var row frame.YankWindow
		if err := json.Unmarshal([]byte(line), &row); err != nil {
			return nil, err
		}
		out = append(out, row)
	}
	return out, scan.Err()
}

func loadRevokes(path string) (map[string]uint64, error) {
	out := map[string]uint64{}
	f, err := os.Open(path)
	if err != nil {
		if os.IsNotExist(err) {
			return out, nil
		}
		return nil, err
	}
	defer f.Close()
	scan := bufio.NewScanner(f)
	for scan.Scan() {
		line := scan.Text()
		if line == "" {
			continue
		}
		var row frame.RevokeRow
		if err := json.Unmarshal([]byte(line), &row); err != nil {
			return nil, err
		}
		out[row.Crate+"@"+row.Vers] = row.At
	}
	return out, scan.Err()
}

func AdvisoryDigest(dataRoot string, gen uint64) (string, error) {
	liveOnly := readBool("/app/config/l7", "adv_live_only", false)
	halfOpen := readString("/app/config/l7", "bound_mode", "closed") == "half_open"
	honor := readBool("/app/config/l7", "honor_revokes", false)
	floor := sevRank(readString("/app/config/l7", "adv_floor", "low"))

	win, err := loadWindows(filepath.Join(dataRoot, "yanks/windows.jsonl"))
	if err != nil {
		return "", err
	}
	revokes, err := loadRevokes(filepath.Join(dataRoot, "yanks/revokes.jsonl"))
	if err != nil {
		return "", err
	}

	active := map[string]bool{}
	_ = halfOpen
	_ = honor
	_ = floor
	for _, w := range win {
		if yankActive(w, gen, false, revokes, false) {
			active[w.Crate+"@"+w.Vers] = true
		}
	}

	f, err := os.Open(filepath.Join(dataRoot, "advisories/feed.jsonl"))
	if err != nil {
		return "", err
	}
	defer f.Close()
	var rows []frame.AdvisoryRow
	scan := bufio.NewScanner(f)
	for scan.Scan() {
		line := scan.Text()
		if line == "" {
			continue
		}
		var row frame.AdvisoryRow
		if err := json.Unmarshal([]byte(line), &row); err != nil {
			return "", err
		}
		if row.From > gen {
			continue
		}
		if liveOnly && !active[row.Crate+"@"+row.Vers] {
			continue
		}
		rows = append(rows, row)
	}
	if err := scan.Err(); err != nil {
		return "", err
	}
	sort.Slice(rows, func(i, j int) bool {
		if rows[i].Crate == rows[j].Crate {
			return rows[i].Vers < rows[j].Vers
		}
		return rows[i].Crate < rows[j].Crate
	})
	payload := map[string]any{"advisories": rows}
	b, err := json.Marshal(payload)
	if err != nil {
		return "", err
	}
	sum := sha256.Sum256(b)
	return hex.EncodeToString(sum[:]), nil
}
