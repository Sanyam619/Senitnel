package main

import (
	"fmt"
	"os"

	"csp.local/reconcile/internal/core"
)

func main() {
	if len(os.Args) < 3 {
		fmt.Fprintf(os.Stderr, "usage: cspd <case> <root>\n")
		os.Exit(2)
	}
	if err := core.ExecN(os.Args[1], os.Args[2]); err != nil {
		fmt.Fprintf(os.Stderr, "case failed: %v\n", err)
		os.Exit(1)
	}
}
