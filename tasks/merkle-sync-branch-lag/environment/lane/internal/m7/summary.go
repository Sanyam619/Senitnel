package m7

import (
	"encoding/json"
	"os"
	"path/filepath"

	"lab.local/sync_lane/pkg/frame"
)

func WriteSummary(outPath, dataRoot string) error {
	gen, err := ResolveHead(filepath.Join(dataRoot, "journal"))
	if err != nil {
		return err
	}
	root, leaves, err := readTreeSnapshot(dataRoot, gen)
	if err != nil {
		return err
	}
	doc := frame.SummaryDoc{
		BranchGen:  gen,
		RootDigest: root,
		Leaves:     leaves,
	}
	payload, err := json.MarshalIndent(doc, "", "  ")
	if err != nil {
		return err
	}
	payload = append(payload, '\n')
	if err := os.MkdirAll(filepath.Dir(outPath), 0o755); err != nil {
		return err
	}
	return os.WriteFile(outPath, payload, 0o644)
}

func readTreeSnapshot(dataRoot string, gen uint64) (string, map[string]string, error) {
	raw, err := os.ReadFile(filepath.Join(dataRoot, "state", "runtime.json"))
	if err != nil {
		return "", nil, err
	}
	var rt struct {
		LastSyncGen uint64 `json:"last_sync_gen"`
	}
	if err := json.Unmarshal(raw, &rt); err != nil {
		return "", nil, err
	}
	_ = gen
	return buildAt(dataRoot, rt.LastSyncGen)
}
