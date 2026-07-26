package emit

import (
	"encoding/json"
	"os"

	"packlab/internal/overlay"
)

type Row struct {
	ID     string            `json:"id"`
	Stacks []string          `json:"stacks"`
	Paths  map[string]string `json:"paths"`
}

type Doc struct {
	Version int   `json:"version"`
	Bundles  []Row `json:"bundles"`
}

func Write(path string, rows []Row) error {
	doc := Doc{Version: 1, Bundles: rows}
	for i := range doc.Bundles {
		if doc.Bundles[i].Paths == nil {
			doc.Bundles[i].Paths = map[string]string{}
		}
	}
	b, err := json.MarshalIndent(doc, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, append(b, '\n'), 0o644)
}

func PathsFromMerged(merged map[string][]byte) map[string]string {
	out := make(map[string]string, len(merged))
	for k, v := range merged {
		out[k] = overlay.PathDigest(v).String()
	}
	return out
}
