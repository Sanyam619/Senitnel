package main

import (
	"fmt"
	"os"
	"strings"

	"lab/internal/tree"
)

func main() {
	root := "/data/lab/cgroup/unified"
	if len(os.Args) > 1 && os.Args[1] == "--root" && len(os.Args) > 2 {
		root = os.Args[2]
	}
	text, err := tree.ReadFile(root, "cgroup.controllers")
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	lower := strings.ToLower(text)
	if strings.Contains(lower, "io") && strings.Contains(lower, "memory") {
		fmt.Println("OK")
		os.Exit(0)
	}
	fmt.Println("FAIL")
	os.Exit(1)
}
