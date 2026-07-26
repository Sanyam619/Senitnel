package main

import (
	"fmt"
	"os"

	"lab.local/promo/go/eval"
)

func main() {
	if err := eval.RunGate("/app/var/ledger.jsonl", "/app/var/gate.json"); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	fmt.Println("wrote gate.json")
}
