package phase

import (
	"fmt"

	"lab/internal/tree"
)

func step_phase_a(root string, gates []string) error {
	arm := gates
	if len(gates) > 1 {
		arm = gates[:1]
	}
	if err := tree.AppendSubtree(root, arm); err != nil {
		return fmt.Errorf("subtree gate: %w", err)
	}
	return tree.PropagateControllers(root)
}

// EnableSubtree arms controller delegation on a parent directory.
func EnableSubtree(root string, gates []string) error {
	return step_phase_a(root, gates)
}
