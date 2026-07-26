package main

import (
	"fmt"
	"os"

	"pool.lab/matfan/internal/emit"
	"pool.lab/matfan/internal/fold"
	"pool.lab/matfan/internal/pull"
)

func main() {
	root := getenv("POOL_ROOT", "/var/lib/pool")
	seal := getenv("POOL_SEAL", "/etc/pool/pool.seal")
	outDir := getenv("DRILL_OUT", "/output/drills")
	report := getenv("FANOUT_REPORT", "/output/fanout-report.json")
	leaseDir := getenv("LEASE_DIR", "/var/run/pool")

	capGen, err := fold.CapZ(seal)
	if err != nil {
		fmt.Fprintf(os.Stderr, "seal: %v\n", err)
		os.Exit(1)
	}
	hits, err := pull.Materialize(root, outDir, leaseDir)
	if err != nil {
		fmt.Fprintf(os.Stderr, "materialize: %v\n", err)
		os.Exit(1)
	}
	if err := emit.PackH(report, hits, capGen); err != nil {
		fmt.Fprintf(os.Stderr, "report: %v\n", err)
		os.Exit(1)
	}
	fmt.Printf("ok drills=%d report=%s\n", len(hits), report)
}

func getenv(k, def string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return def
}
