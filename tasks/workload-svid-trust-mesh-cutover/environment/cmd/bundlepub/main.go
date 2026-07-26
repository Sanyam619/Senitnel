package main

import (
	"fmt"
	"os"

	"meshlab/k9"
)

func main() {
	rt := envOr("MESH_RUNTIME", "/app/data/state/runtime.json")
	live := envOr("MESH_LIVE", "/app/data/state/live-bundle.json")
	if err := k9.Apply(rt, live); err != nil {
		fmt.Fprintf(os.Stderr, "bundlepub: %v\n", err)
		os.Exit(1)
	}
	fmt.Println("bundlepub: ok")
}

func envOr(k, def string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return def
}
