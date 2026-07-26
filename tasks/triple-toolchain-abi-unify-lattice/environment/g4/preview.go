package main

import (
	"fmt"
	"os"
	"path/filepath"
)

// preview lists profile filenames for status_check.sh; does not resolve live path.
func previewProfiles(root string) ([]string, error) {
	entries, err := os.ReadDir(filepath.Join(root, "config", "profiles"))
	if err != nil {
		return nil, err
	}
	var out []string
	for _, e := range entries {
		if !e.IsDir() {
			out = append(out, e.Name())
		}
	}
	return out, nil
}

func dumpPreview() {
	names, err := previewProfiles("/app")
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return
	}
	for _, n := range names {
		fmt.Println(n)
	}
}
