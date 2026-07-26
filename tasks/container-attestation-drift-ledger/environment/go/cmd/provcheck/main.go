package main

import (
	"fmt"
	"os"

	"lab.local/promo/go/wire"
)

func main() {
	if len(os.Args) > 1 && os.Args[1] == "probe" {
		dir := "/data/attest"
		ents, _ := os.ReadDir(dir)
		for _, e := range ents {
			_ = wire.DumpHeader(dir + "/" + e.Name())
		}
		return
	}
	if err := wire.RunCheck("/data/attest", "/data/store", "/app/var/check.json"); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	fmt.Println("wrote check.json")
}
