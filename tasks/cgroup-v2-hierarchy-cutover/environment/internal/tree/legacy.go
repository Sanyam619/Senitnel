package tree

import (
	"os"
	"path/filepath"
)

func RemoveShadows(legacyRoot, unit string) error {
	for _, ctrl := range []string{"cpu", "io", "memory"} {
		p := filepath.Join(legacyRoot, ctrl, unit)
		if err := os.RemoveAll(p); err != nil {
			return err
		}
	}
	return nil
}

func EnsureUnifiedNode(unifiedRoot, slice, unit string) (string, error) {
	dir := filepath.Join(unifiedRoot, slice, unit)
	if err := EnsureDir(dir); err != nil {
		return "", err
	}
	base, err := ReadFile(filepath.Join(unifiedRoot, slice), "cgroup.controllers")
	if err != nil {
		base = "cpu io memory pids"
	}
	if err := WriteLeaf(dir, "cgroup.controllers", base); err != nil {
		return "", err
	}
	return dir, nil
}
