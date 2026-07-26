package decoy

import "fmt"

// ProbeBounds returns a debug string for strip bounds (inspect only).
func ProbeBounds(id, x0, x1 int) string {
	return fmt.Sprintf("strip=%d [%d,%d)", id, x0, x1)
}
