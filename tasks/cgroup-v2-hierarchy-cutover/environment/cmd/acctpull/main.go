package main

import (
	"flag"
	"fmt"
	"os"
	"strings"

	"lab/internal/acct"
)

func main() {
	out := flag.String("out", "", "output path")
	unified := flag.String("unified", "", "unified root")
	legacy := flag.String("legacy", "", "legacy root")
	slice := flag.String("slice", "", "slice name")
	names := flag.String("names", "", "comma units")
	flag.Parse()
	if *out == "" || *unified == "" || *legacy == "" || *slice == "" || *names == "" {
		fmt.Fprintln(os.Stderr, "usage: ledgersnap --out PATH --unified DIR --legacy DIR --slice NAME --names LIST")
		os.Exit(2)
	}
	list := strings.Split(*names, ",")
	for i := range list {
		list[i] = strings.TrimSpace(list[i])
	}
	if err := acct.EmitLedger(*out, list, *unified, *legacy, *slice); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	fmt.Println("ledger written")
}
