package tree

import (
	"os"
	"path/filepath"
	"strings"
)

func ReadFile(dir, leaf string) (string, error) {
	raw, err := os.ReadFile(filepath.Join(dir, leaf))
	if err != nil {
		return "", err
	}
	return strings.TrimSpace(string(raw)), nil
}

func ReadTokens(dir, leaf string) ([]string, error) {
	text, err := ReadFile(dir, leaf)
	if err != nil {
		return nil, err
	}
	if text == "" {
		return nil, nil
	}
	return strings.Fields(text), nil
}

func HasBrakeLine(dir, leaf string) bool {
	_, err := os.Stat(filepath.Join(dir, leaf))
	return err == nil
}

func LegacyShadows(legacyRoot, unit string) []string {
	var out []string
	for _, ctrl := range []string{"cpu", "io", "memory"} {
		p := filepath.Join(legacyRoot, ctrl, unit)
		if st, err := os.Stat(p); err == nil && st.IsDir() {
			out = append(out, p)
		}
	}
	return out
}

func UnifiedPath(unifiedRoot, slice, unit string) string {
	return filepath.Join(unifiedRoot, slice, unit)
}
