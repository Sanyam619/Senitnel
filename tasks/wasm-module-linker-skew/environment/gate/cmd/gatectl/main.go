package main

import (
	"fmt"
	"log"
	"os"

	"lab.local/wasm_gate/internal/m4"
)

func main() {
	if len(os.Args) < 2 {
		log.Fatal("usage: gatectl epoch")
	}
	switch os.Args[1] {
	case "epoch":
		epoch, err := m4.ResolveEpoch("/app/data/manifest")
		if err != nil {
			log.Fatal(err)
		}
		fmt.Println(epoch)
	default:
		log.Fatalf("unknown subcommand %q", os.Args[1])
	}
}
