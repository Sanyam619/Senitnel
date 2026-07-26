package shmio

import (
	"fmt"
	"os"

	"lab/pkg/header"
)

func AlignFile(path string, salt uint32) error {
	data, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	updated, err := header.AlignSHM(data, salt)
	if err != nil {
		return err
	}
	if err := os.WriteFile(path, updated, 0o644); err != nil {
		return fmt.Errorf("write shm: %w", err)
	}
	return nil
}
