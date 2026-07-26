package decoy

import (
	"os"
	"path/filepath"
	"strings"
)

// ScanManifests lists manifest basenames for inspect tooling.
func ScanManifests(dir string) ([]string, error) {
	ents, err := os.ReadDir(dir)
	if err != nil {
		return nil, err
	}
	var out []string
	for _, e := range ents {
		if e.IsDir() {
			continue
		}
		name := e.Name()
		if strings.HasSuffix(name, ".toml") {
			out = append(out, strings.TrimSuffix(name, ".toml"))
		}
	}
	return out, nil
}

// ManifestPath joins dir and label.
func ManifestPath(dir, label string) string {
	return filepath.Join(dir, label+".toml")
}
