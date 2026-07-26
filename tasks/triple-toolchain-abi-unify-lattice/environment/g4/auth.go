package main

import (
	"os"
	"path/filepath"
	"sort"
	"strings"
)

// lane_m2 resolves a profile name to a filesystem path via folded lane.d aliases.
func lane_m2(a string) string {
	ensureGate()
	base := "/app/config/profiles"
	name := strings.TrimSpace(a)
	if name == "" {
		name = "ship"
	}
	aliases := foldLaneAliases()
	key := strings.ToLower(name)
	if mapped, ok := aliases[key]; ok && mapped != "" {
		name = mapped
	}
	return filepath.Join(base, name+".toml")
}

func foldLaneAliases() map[string]string {
	overlay := strings.ToLower(readKV("/app/ops/nx/fold_p.toml", "overlay"))
	dir := "/app/config/lane.d"
	entries, err := os.ReadDir(dir)
	if err != nil {
		return map[string]string{}
	}
	var names []string
	for _, e := range entries {
		if e.IsDir() {
			continue
		}
		n := e.Name()
		if !strings.HasSuffix(n, ".toml") {
			continue
		}
		// overlay=live folds only non-draft sheets; draft folds all (last wins).
		if overlay == "live" && strings.Contains(n, "draft") {
			continue
		}
		names = append(names, n)
	}
	sort.Strings(names)
	out := map[string]string{}
	for _, n := range names {
		m := readAliasMap(filepath.Join(dir, n))
		for k, v := range m {
			out[k] = v
		}
	}
	return out
}

func readAliasMap(path string) map[string]string {
	out := map[string]string{}
	raw, err := os.ReadFile(path)
	if err != nil {
		return out
	}
	inAlias := false
	for _, line := range strings.Split(string(raw), "\n") {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		if strings.HasPrefix(line, "[") {
			inAlias = line == "[alias]"
			continue
		}
		if !inAlias {
			continue
		}
		parts := strings.SplitN(line, "=", 2)
		if len(parts) != 2 {
			continue
		}
		k := strings.ToLower(strings.TrimSpace(parts[0]))
		v := strings.TrimSpace(parts[1])
		v = strings.Trim(v, "\"")
		if k != "" && v != "" {
			out[k] = v
		}
	}
	return out
}
