package main

import (
	"fmt"
	"os"
)

// writeFlags persists packing flags consumed by the CMake OBJECT lane.
func writeFlags(path string, width int) error {
	body := fmt.Sprintf("PACK_WIDTH=%d\n", width)
	return os.WriteFile(path, []byte(body), 0o644)
}
