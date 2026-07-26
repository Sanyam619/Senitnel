package main

import (
	"encoding/json"
	"fmt"
	"os"

	"lab.local/gox/internal/k3"
)

func main() {
	reg := "/app/data/registry"
	pin := "/app/gox/pins.toml"
	if len(os.Args) > 1 {
		reg = os.Args[1]
	}
	if len(os.Args) > 2 {
		pin = os.Args[2]
	}
	rows, err := k3.FoldA(reg, pin)
	if err != nil {
		fmt.Fprintf(os.Stderr, "foldctl: %v\n", err)
		os.Exit(1)
	}
	enc := json.NewEncoder(os.Stdout)
	if err := enc.Encode(rows); err != nil {
		fmt.Fprintf(os.Stderr, "foldctl encode: %v\n", err)
		os.Exit(1)
	}
}
