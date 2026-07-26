package main

import (
	"flag"
	"fmt"
	"log"
	"os"

	"lab.local/raft_fork_lane/internal/m7"
)

func main() {
	if len(os.Args) < 2 {
		log.Fatal("usage: lane head|emit")
	}
	switch os.Args[1] {
	case "head":
		gen, err := m7.ResolveBranch("/app/data/manifests", "events")
		if err != nil {
			log.Fatal(err)
		}
		fmt.Println(gen)
	case "emit":
		fs := flag.NewFlagSet("emit", flag.ExitOnError)
		out := fs.String("out", "", "output path")
		_ = fs.Parse(os.Args[2:])
		if *out == "" {
			log.Fatal("emit requires --out")
		}
		if err := m7.WriteSummary(*out); err != nil {
			log.Fatal(err)
		}
	default:
		log.Fatalf("unknown subcommand %q", os.Args[1])
	}
}
