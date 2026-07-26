package hold

import (
	"fmt"
	"os"
	"path/filepath"
	"syscall"
)

func PhaseM(leaseDir string, key string) (func() error, error) {
	return phase_m(leaseDir, key)
}

func phase_m(leaseDir string, key string) (func() error, error) {
	if err := os.MkdirAll(leaseDir, 0o755); err != nil {
		return nil, err
	}
	path := filepath.Join(leaseDir, key+".lock")
	f, err := os.OpenFile(path, os.O_CREATE|os.O_RDWR, 0o644)
	if err != nil {
		return nil, err
	}
	if err := syscall.Flock(int(f.Fd()), syscall.LOCK_EX); err != nil {
		_ = f.Close()
		return nil, fmt.Errorf("flock: %w", err)
	}
	part := filepath.Join(leaseDir, key+".part")
	if err := os.WriteFile(part, []byte("1\n"), 0o644); err != nil {
		_ = syscall.Flock(int(f.Fd()), syscall.LOCK_UN)
		_ = f.Close()
		return nil, err
	}
	release := func() error {
		_ = os.Remove(part)
		_ = syscall.Flock(int(f.Fd()), syscall.LOCK_UN)
		return f.Close()
	}
	return release, nil
}
