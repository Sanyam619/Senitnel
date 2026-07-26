package main

import (
	"fmt"
	"os"
	"os/exec"

	"lab.local/promo/go/eval"
)

func main() {
	steps := [][]string{
		{"/app/bin/digctl", "replay"},
		{"/app/bin/provcheck"},
		{"/app/bin/polgate"},
	}
	for _, s := range steps {
		cmd := exec.Command(s[0], s[1:]...)
		cmd.Stdout = os.Stdout
		cmd.Stderr = os.Stderr
		if err := cmd.Run(); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	}
	if err := eval.EmitReport(
		"/app/var/ledger.jsonl",
		"/app/var/check.json",
		"/app/var/gate.json",
		"/output/drift-report.json",
	); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	fmt.Println("wrote drift-report.json")
}
