package internal

import (
	"os"
	"path/filepath"
	"strconv"
	"strings"
)

// RowW carries the roots directory and the value the root lines up with.
type RowW struct {
	Dir   string
	Bound int64
}

// SlotW carries the resolved root generation and whether it lines up.
type SlotW struct {
	Anchor int64
	Ok     bool
}

func slot_w(a RowW, b *SlotW) error {
	raw, err := os.ReadFile(filepath.Join(a.Dir, "live.bundle"))
	if err != nil {
		return err
	}
	b.Anchor = bundleGen(raw)
	b.Ok = b.Anchor == a.Bound
	return nil
}

func bundleGen(raw []byte) int64 {
	for _, line := range strings.Split(string(raw), "\n") {
		line = strings.TrimSpace(line)
		if strings.HasPrefix(line, "gen=") {
			if n, err := strconv.ParseInt(strings.TrimSpace(line[4:]), 10, 64); err == nil {
				return n
			}
		}
	}
	return -1
}
