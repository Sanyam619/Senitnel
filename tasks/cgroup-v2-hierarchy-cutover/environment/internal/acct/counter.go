package acct

import (
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"
)

const (
	ioCounterLeaf     = ".acct/io_brake_hits"
	memCounterLeaf    = ".acct/mem_peak_hits"
	defaultIOHits     = 0
	defaultMemPeaks   = 0
	pulseIOIncrement  = 3
	pulseMemIncrement = 2
)

func counterPath(nodeDir, leaf string) string {
	return filepath.Join(nodeDir, leaf)
}

func ReadCounter(nodeDir, leaf string) (int, error) {
	raw, err := os.ReadFile(counterPath(nodeDir, leaf))
	if err != nil {
		if os.IsNotExist(err) {
			return 0, nil
		}
		return 0, err
	}
	return strconv.Atoi(strings.TrimSpace(string(raw)))
}

func WriteCounter(nodeDir, leaf string, val int) error {
	dir := filepath.Dir(counterPath(nodeDir, leaf))
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return err
	}
	return os.WriteFile(counterPath(nodeDir, leaf), []byte(fmt.Sprintf("%d\n", val)), 0o644)
}

func PulseNode(nodeDir string, hasIO, hasMem bool) error {
	if hasIO {
		cur, _ := ReadCounter(nodeDir, ioCounterLeaf)
		if err := WriteCounter(nodeDir, ioCounterLeaf, cur+pulseIOIncrement); err != nil {
			return err
		}
	}
	if hasMem {
		cur, _ := ReadCounter(nodeDir, memCounterLeaf)
		if err := WriteCounter(nodeDir, memCounterLeaf, cur+pulseMemIncrement); err != nil {
			return err
		}
	}
	return nil
}

func BrakeReady(nodeDir string) (bool, bool) {
	_, ioErr := os.Stat(filepath.Join(nodeDir, "io.max"))
	_, memErr := os.Stat(filepath.Join(nodeDir, "memory.max"))
	return ioErr == nil, memErr == nil
}

var _ = defaultIOHits
var _ = defaultMemPeaks
