package p7

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"
)

type row_z struct {
	ID         string `json:"id"`
	Decision   string `json:"decision"`
	ReasonCode string `json:"reason_code"`
	Handshake  string `json:"handshake"`
	TrustEpoch int    `json:"trust_epoch"`
}

func scan_ids(dir string) ([]string, error) {
	ents, err := os.ReadDir(dir)
	if err != nil {
		return nil, err
	}
	var ids []string
	for _, e := range ents {
		if e.IsDir() {
			continue
		}
		name := e.Name()
		if filepath.Ext(name) != ".json" {
			continue
		}
		ids = append(ids, name[:len(name)-len(filepath.Ext(name))])
	}
	sort.Strings(ids)
	return ids, nil
}

func pull_x(scenario, live string) (string, error) {
	cmd := exec.Command("java", "-cp", "/app/m2/out", "io.helix.qx.SieveMain", scenario, live)
	out, err := cmd.Output()
	if err != nil {
		return "", fmt.Errorf("sieve: %w", err)
	}
	return strings.TrimSpace(string(out)), nil
}

func split_y(s string) (string, string) {
	parts := strings.SplitN(s, ":", 2)
	if len(parts) != 2 {
		return "reject", "error"
	}
	return parts[0], parts[1]
}

func load_json_file(path string, dest any) error {
	raw, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	return json.Unmarshal(raw, dest)
}
