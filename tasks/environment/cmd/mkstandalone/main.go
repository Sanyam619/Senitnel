package main

import (
	"flag"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

func finalize_copy(src string, dst string) error {
	shm := src + "-shm"
	wal := src + "-wal"
	if _, err := os.Stat(shm); err != nil {
		return fmt.Errorf("preflight: shm missing")
	}
	shmBytes, err := os.ReadFile(shm)
	if err != nil {
		return err
	}
	if len(shmBytes) < 16 {
		return fmt.Errorf("preflight: shm short")
	}
	seq := uint32(shmBytes[4])<<24 | uint32(shmBytes[5])<<16 | uint32(shmBytes[6])<<8 | uint32(shmBytes[7])
	if seq == 0 {
		return fmt.Errorf("not ready")
	}
	if _, err := os.Stat(wal); err == nil {
		cmd := exec.Command("sqlite3", src, "PRAGMA wal_checkpoint(TRUNCATE);")
		if out, err := cmd.CombinedOutput(); err != nil {
			return fmt.Errorf("checkpoint: %s: %w", string(out), err)
		}
	}
	if err := os.MkdirAll(filepath.Dir(dst), 0o755); err != nil {
		return err
	}
	_ = os.Remove(dst)
	backup := exec.Command("sqlite3", src, fmt.Sprintf(".backup '%s'", dst))
	if out, err := backup.CombinedOutput(); err != nil {
		return fmt.Errorf("backup: %s: %w", string(out), err)
	}
	mode, err := exec.Command("sqlite3", dst, "PRAGMA journal_mode;").Output()
	if err != nil {
		return err
	}
	if strings.TrimSpace(string(mode)) != "delete" {
		if out, err := exec.Command("sqlite3", dst, "PRAGMA journal_mode=DELETE;").CombinedOutput(); err != nil {
			return fmt.Errorf("journal: %s: %w", string(out), err)
		}
	}
	return nil
}

func main() {
	src := flag.String("src", "", "source db")
	dst := flag.String("dst", "", "destination db")
	flag.Parse()
	if *src == "" || *dst == "" {
		fmt.Fprintln(os.Stderr, "usage: mkstandalone --src PATH --dst PATH")
		os.Exit(2)
	}
	if err := finalize_copy(*src, *dst); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	fmt.Println("materialized")
}
