package main

import (
	"fmt"
	"os"

	"meshlab/p7"
)

func main() {
	scenarios := envOr("MESH_SCENARIOS", "/app/data/scenarios")
	outPath := envOr("MESH_OUT", "/output/mesh-cutover.json")
	if err := p7.Apply(scenarios, outPath); err != nil {
		fmt.Fprintf(os.Stderr, "probe: %v\n", err)
		os.Exit(1)
	}
}

func envOr(k, def string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return def
}
