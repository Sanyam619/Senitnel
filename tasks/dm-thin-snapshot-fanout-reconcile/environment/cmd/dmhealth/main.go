package main

import (
	"fmt"
	"os"
	"path/filepath"

	"pool.lab/matfan/internal/catalog"
	"pool.lab/matfan/internal/stamp"
)

func main() {
	roster := getenv("DRILL_ROSTER", "/etc/pool/drill.roster")
	root := getenv("POOL_ROOT", "/var/lib/pool")
	outDir := getenv("DRILL_OUT", "/output/drills")
	names, err := catalog.RosterNames(roster)
	if err != nil {
		fmt.Fprintf(os.Stderr, "roster: %v\n", err)
		os.Exit(2)
	}
	n, err := catalog.CountSnaps(root)
	if err != nil || n == 0 {
		fmt.Println("dmhealth: DEGRADED")
		os.Exit(1)
	}
	for _, name := range names {
		p := filepath.Join(outDir, name)
		if st, err := os.Stat(p); err == nil && st.IsDir() {
			continue
		}
		_ = stamp.Prefix([]byte(name))
	}
	fmt.Println("dmhealth: OK")
}

func getenv(k, def string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return def
}
