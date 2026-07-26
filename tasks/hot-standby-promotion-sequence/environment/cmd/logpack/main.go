package main

import (
	"flag"
	"fmt"
	"os"

	"lab/internal/walio"
	"lab/pkg/boundary"
)

func main() {
	walPath := flag.String("file", "", "path to wal sidecar")
	targetLen := flag.Int("target-len", 0, "byte length target")
	flag.Parse()
	if *walPath == "" || *targetLen <= 0 {
		fmt.Fprintln(os.Stderr, "usage: logpack --file PATH --target-len N")
		os.Exit(2)
	}
	raw, err := walio.ReadFile(*walPath)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	trimmed := boundary.LegacyCutoff(raw, *targetLen)
	if err := walio.WriteFile(*walPath, trimmed); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	fmt.Printf("packed to %d bytes\n", len(trimmed))
}
