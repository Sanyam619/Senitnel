package main

import (
	"flag"
	"fmt"
	"os"
	"strings"

	"lab/pkg/phase"
	"lab/pkg/relay"
)

var defaultBrakes = map[string]string{
	"io.max":     "8:1048576",
	"memory.max": "33554432",
}

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: slicearm arm|bind ...")
		os.Exit(2)
	}
	switch os.Args[1] {
	case "arm":
		runArm(os.Args[2:])
	case "bind":
		runBind(os.Args[2:])
	default:
		fmt.Fprintln(os.Stderr, "unknown subcommand")
		os.Exit(2)
	}
}

func runArm(args []string) {
	fs := flag.NewFlagSet("arm", flag.ExitOnError)
	parent := fs.String("parent", "", "parent dir")
	add := fs.String("add", "", "comma gates")
	_ = fs.Parse(args)
	if *parent == "" || *add == "" {
		fmt.Fprintln(os.Stderr, "usage: slicearm arm --parent DIR --add GATES")
		os.Exit(2)
	}
	tokens := strings.Split(*add, ",")
	for i := range tokens {
		tokens[i] = strings.TrimSpace(tokens[i])
	}
	if err := phase.EnableSubtree(*parent, tokens); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	fmt.Println("armed")
}

func runBind(args []string) {
	fs := flag.NewFlagSet("bind", flag.ExitOnError)
	legacy := fs.String("legacy", "", "legacy root")
	unified := fs.String("unified", "", "unified root")
	slice := fs.String("slice", "", "slice")
	unit := fs.String("unit", "", "unit name")
	_ = fs.Parse(args)
	if *legacy == "" || *unified == "" || *slice == "" || *unit == "" {
		fmt.Fprintln(os.Stderr, "usage: slicearm bind --legacy DIR --unified DIR --slice NAME --unit NAME")
		os.Exit(2)
	}
	if err := relay.WireNode(*legacy, *unified, *slice, *unit, defaultBrakes); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	fmt.Println("bound")
}
