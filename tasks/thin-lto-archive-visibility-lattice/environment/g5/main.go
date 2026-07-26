package main

import (
	"fmt"
	"os"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: archctl <resolve|members|emit|digest> ...")
		os.Exit(2)
	}
	switch os.Args[1] {
	case "resolve":
		os.Exit(runResolve(os.Args[2:]))
	case "members":
		os.Exit(runMembers(os.Args[2:]))
	case "emit":
		os.Exit(runEmit(os.Args[2:]))
	case "digest":
		os.Exit(runDigest(os.Args[2:]))
	case "preview":
		printPreview()
	default:
		fmt.Fprintln(os.Stderr, "unknown subcommand")
		os.Exit(2)
	}
}

func atoi(s string) int {
	n := 0
	for _, c := range s {
		if c < '0' || c > '9' {
			return 0
		}
		n = n*10 + int(c-'0')
	}
	return n
}
