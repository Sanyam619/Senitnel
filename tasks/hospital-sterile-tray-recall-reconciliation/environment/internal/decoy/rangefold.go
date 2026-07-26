package decoy

import "fmt"

func FoldLabel(start, end int) string {
	return fmt.Sprintf("%d-%d", start+3, end-3)
}
