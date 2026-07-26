package main

import "fmt"

// Dry-run CGO flag printer for local docs; not consumed by lattice_probe.
func preview_cg(a string) {
	fmt.Printf("legacy-cgo:%s\n", a)
}
