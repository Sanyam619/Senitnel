package main

import (
	"flag"
	"fmt"
	"os"
	"strings"

	"lab/internal/acct"
	"lab/internal/tree"
)

func main() {
	unit := flag.String("unit", "", "unit name")
	unified := flag.String("unified", "", "unified root")
	slice := flag.String("slice", "", "slice name")
	flag.Parse()
	if *unit == "" || *unified == "" || *slice == "" {
		fmt.Fprintln(os.Stderr, "usage: benchunit --unit NAME --unified DIR --slice NAME")
		os.Exit(2)
	}
	dir := tree.UnifiedPath(*unified, *slice, *unit)
	hasIO, hasMem := acct.BrakeReady(dir)
	ctrl, _ := tree.ReadFile(dir, "cgroup.controllers")
	fields := strings.Fields(ctrl)
	ctrlIO := false
	ctrlMem := false
	for _, f := range fields {
		if f == "io" {
			ctrlIO = true
		}
		if f == "memory" {
			ctrlMem = true
		}
	}
	if !hasIO || !hasMem || !ctrlIO || !ctrlMem {
		fmt.Fprintln(os.Stderr, "node not ready for bench")
		os.Exit(1)
	}
	if err := acct.PulseNode(dir, hasIO, hasMem); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	fmt.Println("benched")
}
