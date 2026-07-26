package main

import (
	"os"
	"path/filepath"
	"strconv"
	"strings"
)

func gateOk() bool {
	cut := "/app/ops/nx/cut_n.toml"
	if readKV(cut, "cutover") != "sealed" {
		return false
	}
	epoch, _ := strconv.ParseInt(readKV(cut, "epoch"), 10, 64)
	floor, _ := strconv.ParseInt(readKV(cut, "epoch_floor"), 10, 64)
	if epoch < floor {
		return false
	}
	hold := readKV(cut, "hold_token")
	want := latestHoldToken("/app/data/fixtures/desk_journal.jsonl")
	return hold != "" && want != "" && hold == want
}

func latestHoldToken(path string) string {
	raw, err := os.ReadFile(path)
	if err != nil {
		return ""
	}
	token := ""
	for _, line := range strings.Split(string(raw), "\n") {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		if !strings.Contains(line, `"event":"hold"`) && !strings.Contains(line, `"event": "hold"`) {
			continue
		}
		if idx := strings.Index(line, `"token"`); idx >= 0 {
			rest := line[idx+7:]
			if colon := strings.Index(rest, ":"); colon >= 0 {
				v := strings.TrimSpace(rest[colon+1:])
				v = strings.TrimPrefix(v, `"`)
				if end := strings.Index(v, `"`); end > 0 {
					token = v[:end]
				}
			}
		}
	}
	return token
}

func rematerializeAll() {
	copyFile("/app/link/lane_seed.toml", "/app/config/lane.d/50-draft.toml")
	copyFile("/app/link/strand_seed.toml", "/app/config/profiles/craft.toml")
	copyFile("/app/link/fleet_seed.toml", "/app/config/profiles/fleet.toml")
	_ = os.WriteFile("/app/ops/nx/pref_a.toml", []byte("prefer = \"archive\"\n"), 0o644)
	_ = os.WriteFile("/app/ops/nx/fold_p.toml", []byte("overlay = \"draft\"\n"), 0o644)
	_ = os.WriteFile("/app/ops/nx/rel_mask.toml", []byte("strip_b_on_release = true\n"), 0o644)
}

func promoteNxLive() {
	copyIfPresent("/app/ops/nx/draft_q.toml", "/app/config/lane.d/50-draft.toml")
	copyIfPresent("/app/ops/nx/strand_q.toml", "/app/config/profiles/craft.toml")
	copyIfPresent("/app/ops/nx/width_q.toml", "/app/config/profiles/fleet.toml")
}

func ensureGate() {
	if gateOk() {
		promoteNxLive()
	} else {
		rematerializeAll()
	}
}

func copyIfPresent(src, dst string) {
	if _, err := os.Stat(src); err != nil {
		return
	}
	copyFile(src, dst)
}

func copyFile(src, dst string) {
	body, err := os.ReadFile(src)
	if err != nil {
		return
	}
	_ = os.MkdirAll(filepath.Dir(dst), 0o755)
	_ = os.WriteFile(dst, body, 0o644)
}

func readKV(path, key string) string {
	raw, err := os.ReadFile(path)
	if err != nil {
		return ""
	}
	for _, line := range strings.Split(string(raw), "\n") {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		parts := strings.SplitN(line, "=", 2)
		if len(parts) != 2 {
			continue
		}
		if strings.TrimSpace(parts[0]) != key {
			continue
		}
		rest := strings.TrimSpace(parts[1])
		rest = strings.Trim(rest, "\"")
		if rest != "" {
			return rest
		}
	}
	return ""
}

func stripBOnRelease() bool {
	v := strings.ToLower(readKV("/app/ops/nx/rel_mask.toml", "strip_b_on_release"))
	return v == "true" || v == "1" || v == "yes"
}
