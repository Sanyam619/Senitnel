package relay

import (
	"fmt"
	"path/filepath"
	"strings"

	"lab/internal/tree"
)

func parentSliceDir(unifiedRoot, slice string) string {
	return filepath.Join(unifiedRoot, slice)
}

func sliceGatesArmed(unifiedRoot, slice string) error {
	parent := parentSliceDir(unifiedRoot, slice)
	tokens, err := tree.ReadTokens(parent, "cgroup.subtree_control")
	if err != nil {
		return fmt.Errorf("slice parent unreadable: %w", err)
	}
	have := map[string]bool{}
	for _, t := range tokens {
		have[strings.ToLower(t)] = true
	}
	for _, need := range []string{"io", "memory"} {
		if !have[need] {
			return fmt.Errorf("slice parent missing %s delegation", need)
		}
	}
	return nil
}
