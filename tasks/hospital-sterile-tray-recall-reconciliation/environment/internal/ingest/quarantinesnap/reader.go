package quarantinesnap

import (
	"encoding/json"
	"os"
	"path/filepath"
)

type Doc struct {
	Version   int      `json:"version"`
	HeldTrays []string `json:"held_trays"`
}

func Load(dir string) (Doc, error) {
	b, err := os.ReadFile(filepath.Join(dir, "quarantine_snap.json"))
	if err != nil {
		return Doc{}, err
	}
	var d Doc
	return d, json.Unmarshal(b, &d)
}
