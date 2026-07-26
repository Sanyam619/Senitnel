package decoy

import "fmt"

// ProbeBounds returns a debug string for strip bounds (inspect only).
func ProbeBounds(id, i0, i1 int) string {
	return fmt.Sprintf("strip=%d [%d,%d)", id, i0, i1)
}
