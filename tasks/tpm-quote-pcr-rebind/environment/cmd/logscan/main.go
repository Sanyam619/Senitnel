package main

import (
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"os"

	"rly/internal/chip"
	"rly/pkg/bind"
	"rly/pkg/trace"
)

func main() {
	traceRoot := flag.String("traces", "/data/traces", "trace dir")
	matrix := flag.String("matrix", "/opt/rly/config/matrix.yaml", "matrix path")
	flag.Parse()

	mat, err := bind.LoadMatrix(*matrix)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	floor, err := bind.FloorRow(mat)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	bench, err := bind.BenchRow(mat)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	pSteps, err := trace.LoadStepsDirect("primary", *traceRoot)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	sSteps, err := trace.LoadStepsDirect("shadow", *traceRoot)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	pRegs, err := chip.RollForwardFixed(pSteps, floor.WalkMode)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	sRegs, err := chip.RollForwardFixed(sSteps, bench.WalkMode)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	match := true
	for _, bank := range floor.Banks {
		if hex.EncodeToString(pRegs[bank]) != hex.EncodeToString(sRegs[bank]) {
			match = false
			break
		}
	}
	out := map[string]any{
		"primary_floor": chip.HexMap(pRegs),
		"shadow_bench":  chip.HexMap(sRegs),
		"chains_match":  match,
	}
	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	_ = enc.Encode(out)
	if !match {
		os.Exit(2)
	}
}
