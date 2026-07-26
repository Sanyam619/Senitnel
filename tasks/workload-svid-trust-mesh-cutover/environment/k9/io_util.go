package k9

import (
	"encoding/json"
	"os"
)

type runtimeView struct {
	Epoch      int    `json:"epoch"`
	AsOf       int64  `json:"as_of"`
	TargetRoot string `json:"target_root"`
}

type liveView struct {
	ActiveRoot string `json:"active_root"`
	Epoch      int    `json:"epoch"`
	Kid        string `json:"kid"`
	Generation int    `json:"generation"`
}

func load_rt(path string) (runtimeView, error) {
	var v runtimeView
	raw, err := os.ReadFile(path)
	if err != nil {
		return v, err
	}
	err = json.Unmarshal(raw, &v)
	return v, err
}

func store_lv(path string, v liveView) error {
	raw, err := json.Marshal(v)
	if err != nil {
		return err
	}
	return os.WriteFile(path, raw, 0o644)
}
