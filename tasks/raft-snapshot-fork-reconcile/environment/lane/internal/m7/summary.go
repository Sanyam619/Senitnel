package m7

import (
	"encoding/json"
	"os"
	"path/filepath"

	"lab.local/raft_fork_lane/pkg/frame"
)

type sidecarDoc struct {
	Digest string `json:"digest"`
}

func WriteSummary(outPath string) error {
	manifestDir := "/app/data/manifests"
	dataRoot := "/app/data"
	gen, err := ResolveBranch(manifestDir, "events")
	if err != nil {
		return err
	}
	eventsStripes, err := stripesAt(manifestDir, "events", gen)
	if err != nil {
		return err
	}
	metricsStripes, err := stripesAt(manifestDir, "metrics", gen)
	if err != nil {
		return err
	}
	eventsDigest, err := readDigest(filepath.Join(dataRoot, "sidecars", "events.idx"))
	if err != nil {
		return err
	}
	metricsDigest, err := readDigest(filepath.Join(dataRoot, "sidecars", "metrics.idx"))
	if err != nil {
		return err
	}
	doc := frame.SummaryDoc{
		RestoredGeneration: gen,
		Events: frame.NamespaceBlock{
			VisibleSegments: uint64(len(eventsStripes)),
			SidecarDigest:  eventsDigest,
		},
		Metrics: frame.NamespaceBlock{
			VisibleSegments: uint64(len(metricsStripes)),
			SidecarDigest:  metricsDigest,
		},
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

func readDigest(path string) (string, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return "", err
	}
	var sc sidecarDoc
	if err := json.Unmarshal(raw, &sc); err != nil {
		return "", err
	}
	return sc.Digest, nil
}
