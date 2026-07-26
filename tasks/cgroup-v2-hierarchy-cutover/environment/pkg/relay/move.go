package relay

import (
	"fmt"
	"path/filepath"

	"lab/internal/tree"
)

func wire_node_b(legacy string, target string, brakes map[string]string) error {
	if legacy != "" {
		unit := filepath.Base(target)
		if err := tree.RemoveShadows(legacy, unit); err != nil {
			return fmt.Errorf("detach: %w", err)
		}
	}
	if err := tree.EnsureDir(target); err != nil {
		return err
	}
	if err := tree.ApplyBrakeMap(target, brakes); err != nil {
		return fmt.Errorf("brakes: %w", err)
	}
	return nil
}

func WireNode(legacyRoot, unifiedRoot, slice, unit string, brakes map[string]string) error {
	if err := sliceGatesArmed(unifiedRoot, slice); err != nil {
		return err
	}
	target, err := tree.EnsureUnifiedNode(unifiedRoot, slice, unit)
	if err != nil {
		return err
	}
	return wire_node_b(legacyRoot, target, brakes)
}
