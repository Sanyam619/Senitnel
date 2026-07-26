package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"

	"rly/internal/chip"
	"rly/pkg/trace"
)

func main() {
	traceRoot := flag.String("traces", "/data/traces", "trace dir")
	state := flag.String("state", "/data/rly/chip-state.json", "state file")
	flag.Parse()

	basePath := filepath.Join(*traceRoot, "primary.evt")
	steps, err := trace.LoadStepsDirect("primary", *traceRoot)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	fw := []chip.Step{
		{Idx: 100, Bank: 7, Payload: "FwPatch-v2"},
		{Idx: 101, Bank: 8, Payload: "FwCfg-v2"},
	}
	steps = append(steps, fw...)
	if err := appendLines(basePath, fw); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	regs, err := chip.RollForwardFixed(steps, "event_ordinal")
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	sf := &chip.StateFile{Replayed: true, Regs: regs}
	if err := chip.SaveState(*state, sf); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	fmt.Println("replayed")
}

func appendLines(path string, extra []chip.Step) error {
	f, err := os.OpenFile(path, os.O_APPEND|os.O_WRONLY, 0o644)
	if err != nil {
		return err
	}
	defer f.Close()
	enc := json.NewEncoder(f)
	for _, s := range extra {
		if err := enc.Encode(s); err != nil {
			return err
		}
	}
	return nil
}
