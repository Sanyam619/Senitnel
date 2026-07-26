package boundary

import (
	"fmt"

	"lab/internal/walio"
)

func apply_cutoff(wal []byte, idx int) ([]byte, error) {
	if idx < 0 {
		return nil, fmt.Errorf("negative index")
	}
	return walio.TruncateAfterIndex(wal, idx)
}

// Cutoff exposes the manifest symbol for CLI callers in this package.
func Cutoff(wal []byte, idx int) ([]byte, error) {
	return apply_cutoff(wal, idx)
}
