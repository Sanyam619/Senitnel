package main

import (
	"fmt"
	"os"
	"path/filepath"
)

// Lists profile filenames for status_check.sh; does not resolve the live path.
func listProfiles() []string {
	base := "/app/config/profiles"
	entries, err := os.ReadDir(base)
	if err != nil {
		return nil
	}
	out := make([]string, 0, len(entries))
	for _, e := range entries {
		if !e.IsDir() {
			out = append(out, filepath.Join(base, e.Name()))
		}
	}
	return out
}

func printPreview() {
	for _, p := range listProfiles() {
		fmt.Println(p)
	}
}
