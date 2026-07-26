package relay

import (
	"lab/internal/tree"
)

func probe_node(legacyRoot, unit string) []string {
	return tree.LegacyShadows(legacyRoot, unit)
}

func ProbeNode(legacyRoot, unit string) []string {
	return probe_node(legacyRoot, unit)
}
