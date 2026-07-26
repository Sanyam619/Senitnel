package k3

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"

	"lab.local/gox/pkg/frame"
)

type metaFile struct {
	Plugins map[string]struct {
		Slots []frame.Row `json:"slots"`
	} `json:"plugins"`
	LiveKey string `json:"live_key"`
}

type yankRow struct {
	Plugin string `json:"plugin"`
	Vers   string `json:"vers"`
	Yanked bool   `json:"yanked"`
}

// FoldA emits layout rows for foldctl from the go lane pin file.
func FoldA(a string, b string) ([]frame.Row, error) {
	reg := a
	if reg == "" {
		reg = "/app/data/registry"
	}
	pinPath := b
	if pinPath == "" {
		pinPath = "/app/gox/pins.toml"
	}
	pin := readPinMap(pinPath)

	pluginKey := pin["plugin_key"]
	honorYanks := pin["honor_yanks"] == "true"
	if pin["mirror_prefer"] == "true" && pin["mirror_plugin"] != "" {
		pluginKey = pin["mirror_plugin"]
	}
	if pin["tag_owner"] == "archive" && pin["archive_plugin"] != "" {
		pluginKey = pin["archive_plugin"]
	}

	yanked := map[string]bool{}
	if honorYanks {
		yankBytes, err := os.ReadFile(filepath.Join(reg, "yanks.jsonl"))
		if err != nil {
			return nil, err
		}
		for _, line := range strings.Split(string(yankBytes), "\n") {
			line = strings.TrimSpace(line)
			if line == "" {
				continue
			}
			var yr yankRow
			if json.Unmarshal([]byte(line), &yr) != nil {
				continue
			}
			if yr.Yanked {
				yanked[yr.Plugin+"@"+yr.Vers] = true
			}
		}
	}

	metaBytes, err := os.ReadFile(filepath.Join(reg, "plugin_meta.json"))
	if err != nil {
		return nil, err
	}
	var meta metaFile
	if err := json.Unmarshal(metaBytes, &meta); err != nil {
		return nil, err
	}

	cand := pluginKey
	if cand == "" {
		if pin["fallback_plugin"] != "" {
			cand = pin["fallback_plugin"]
		} else {
			cand = meta.LiveKey
		}
	}
	if cand == "" {
		cand = "pg-core@0.9.2"
	}
	// Preferring a yanked mirror must fail closed; do not silently fall back.
	if honorYanks && yanked[cand] {
		if pin["mirror_prefer"] == "true" {
			return nil, os.ErrInvalid
		}
		if pin["fallback_plugin"] != "" {
			cand = pin["fallback_plugin"]
		} else {
			cand = meta.LiveKey
		}
	}
	if honorYanks && yanked[cand] {
		return nil, os.ErrInvalid
	}
	plug, ok := meta.Plugins[cand]
	if !ok {
		return nil, os.ErrNotExist
	}
	out := make([]frame.Row, len(plug.Slots))
	copy(out, plug.Slots)
	return out, nil
}

func readPinMap(path string) map[string]string {
	out := map[string]string{}
	raw, err := os.ReadFile(path)
	if err != nil {
		return out
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
		k := strings.TrimSpace(parts[0])
		v := strings.Trim(strings.TrimSpace(parts[1]), `"`)
		out[k] = v
	}
	return out
}
