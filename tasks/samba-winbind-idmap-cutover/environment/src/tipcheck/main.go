package main

import (
	"encoding/binary"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// Observation runner: dumps opaque tip records for discovery. Does not fold.

func main() {
	root := getenv("SAMBA_VAR", "/var/lib/samba")
	etc := getenv("SAMBA_ETC", "/etc/samba")
	sealB, err := os.ReadFile(getenv("DESK_SEAL", filepath.Join(etc, "desk.seal")))
	if err != nil {
		fmt.Fprintf(os.Stderr, "tipcheck: %v\n", err)
		os.Exit(1)
	}
	var sealN int
	fmt.Sscanf(strings.TrimSpace(string(sealB)), "%d", &sealN)

	b, err := os.ReadFile(filepath.Join(root, "journal", "tips.bin"))
	if err != nil {
		fmt.Fprintf(os.Stderr, "tipcheck: %v\n", err)
		os.Exit(1)
	}
	if len(b) < 8 || string(b[:4]) != "TIP2" {
		fmt.Fprintf(os.Stderr, "tipcheck: bad magic\n")
		os.Exit(1)
	}
	n := int(binary.BigEndian.Uint32(b[4:8]))
	off := 8
	fmt.Printf("desk.seal=%d record_count=%d\n", sealN, n)
	for i := 0; i < n; i++ {
		gen := int(binary.BigEndian.Uint16(b[off : off+2]))
		rk := int(b[off+2])
		flags := int(b[off+3])
		off += 4
		knLen := int(b[off])
		off++
		kn := string(b[off : off+knLen])
		off += knLen
		lo := int(binary.BigEndian.Uint32(b[off : off+4]))
		hi := int(binary.BigEndian.Uint32(b[off+4 : off+8]))
		off += 8
		tag := "-"
		if flags&1 != 0 {
			tl := int(b[off])
			off++
			tag = string(b[off : off+tl])
			off += tl
		}
		fmt.Printf("ord=%d gen=%d rk=%d kn=%s lo=%d hi=%d tag=%s\n",
			i, gen, rk, kn, lo, hi, tag)
	}
}

func getenv(k, d string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return d
}
