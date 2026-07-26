package phase

import (
	"path/filepath"

	"lab/internal/tree"
)

func LeafGate(child string, gates []string) error {
	body := ""
	for i, g := range gates {
		if i > 0 {
			body += " "
		}
		body += g
	}
	return tree.WriteLeaf(child, "cgroup.subtree_control", body)
}

func LegacyRelay(unifiedRoot, slice, unit string, gates []string) error {
	dir := filepath.Join(unifiedRoot, slice, unit)
	return LeafGate(dir, gates)
}
