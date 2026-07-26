package main

import (
	"encoding/binary"
	"fmt"
	"os"
	"path/filepath"
)

// Observation runner: dumps opaque ops-journal rows. Does not arm cutover.

func main() {
	root := getenv("SAMBA_VAR", "/var/lib/samba")
	b, err := os.ReadFile(filepath.Join(root, "ops", "journal.bin"))
	if err != nil {
		fmt.Fprintf(os.Stderr, "jrnlcheck: %v\n", err)
		os.Exit(1)
	}
	if len(b) < 8 || string(b[:4]) != "JRN2" {
		fmt.Fprintf(os.Stderr, "jrnlcheck: bad magic\n")
		os.Exit(1)
	}
	n := int(binary.BigEndian.Uint32(b[4:8]))
	off := 8
	fmt.Printf("record_count=%d\n", n)
	for i := 0; i < n; i++ {
		kind := int(b[off])
		mode := int(b[off+1])
		gen := int(binary.BigEndian.Uint16(b[off+2 : off+4]))
		off += 4
		hl := int(b[off])
		off++
		hold := string(b[off : off+hl])
		off += hl
		kindS, modeS := "abort", "rollback"
		if kind == 2 {
			kindS = "cutover"
		}
		if mode == 2 {
			modeS = "seal"
		}
		fmt.Printf("ord=%d kind=%s mode=%s gen=%d hold=%s\n", i, kindS, modeS, gen, hold)
	}
}

func getenv(k, d string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return d
}
