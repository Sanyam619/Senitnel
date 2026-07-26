package decoy

import "fmt"

// TracePartial formats a partial sum for smoke logs.
func TracePartial(id int, s0 float64) string {
	return fmt.Sprintf("part=%d s0=%.6e", id, s0)
}
