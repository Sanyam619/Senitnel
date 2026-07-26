package main

import (
	"fmt"
	"log"
	"os"

	"lab.local/pkg_scan/internal/m4"
)

func main() {
	if len(os.Args) < 2 {
		log.Fatal("usage: advscan window|digest")
	}
	switch os.Args[1] {
	case "window":
		gen, err := m4.ResolveHead("/app/data/index/snapshots")
		if err != nil {
			log.Fatal(err)
		}
		fmt.Println(gen)
	case "digest":
		gen, err := m4.ResolveHead("/app/data/index/snapshots")
		if err != nil {
			log.Fatal(err)
		}
		digest, err := m4.AdvisoryDigest("/app/data", gen)
		if err != nil {
			log.Fatal(err)
		}
		fmt.Println(digest)
	default:
		log.Fatalf("unknown subcommand %q", os.Args[1])
	}
}
