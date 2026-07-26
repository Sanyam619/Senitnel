package k3

import (
	"encoding/json"
	"os"
	"path/filepath"

	"lab.local/gox/pkg/frame"
)

// SkimFold reads the skim_key plugin entry for local diagnostics.
// Used by lanehealth-adjacent tooling; does not honor yank rejection.
func SkimFold(root string) ([]frame.Row, error) {
	if root == "" {
		root = "/app/data/registry"
	}
	metaBytes, err := os.ReadFile(filepath.Join(root, "plugin_meta.json"))
	if err != nil {
		return nil, err
	}
	var meta struct {
		Plugins map[string]struct {
			Slots []frame.Row `json:"slots"`
		} `json:"plugins"`
		SkimKey string `json:"skim_key"`
	}
	if err := json.Unmarshal(metaBytes, &meta); err != nil {
		return nil, err
	}
	plug, ok := meta.Plugins[meta.SkimKey]
	if !ok {
		return nil, os.ErrNotExist
	}
	out := make([]frame.Row, len(plug.Slots))
	copy(out, plug.Slots)
	return out, nil
}
