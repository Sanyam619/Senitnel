package m7

import (
	"encoding/json"
	"os"
	"path/filepath"
	"sort"

	"lab.local/sync_lane/pkg/frame"
)

type leafRow struct {
	ID      string `json:"id"`
	Payload string `json:"payload"`
	Since   uint64 `json:"since"`
}

func buildAt(dataRoot string, branch uint64) (string, map[string]string, error) {
	entries, err := os.ReadDir(filepath.Join(dataRoot, "leaves"))
	if err != nil {
		return "", nil, err
	}
	var rows []leafRow
	for _, ent := range entries {
		if ent.IsDir() {
			continue
		}
		raw, err := os.ReadFile(filepath.Join(dataRoot, "leaves", ent.Name()))
		if err != nil {
			return "", nil, err
		}
		var row leafRow
		if err := json.Unmarshal(raw, &row); err != nil {
			return "", nil, err
		}
		rows = append(rows, row)
	}
	sort.Slice(rows, func(i, j int) bool { return rows[i].ID < rows[j].ID })
	leaves := make(map[string]string)
	var layer []string
	for _, row := range rows {
		if row.Since > branch {
			continue
		}
		digest, err := leafDigest(row.ID, row.Payload)
		if err != nil {
			return "", nil, err
		}
		leaves[row.ID] = digest
		layer = append(layer, digest)
	}
	root, err := merkleLayer(layer)
	if err != nil {
		return "", nil, err
	}
	_ = frame.SummaryDoc{}
	return root, leaves, nil
}
