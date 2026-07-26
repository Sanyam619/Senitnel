package main

import (
	"fmt"
	"os"
)

func runEmit(args []string) int {
	if len(args) < 2 {
		return 2
	}
	if err := writeFlags(args[0], atoi(args[1])); err != nil {
		fmt.Fprintln(os.Stderr, err)
		return 1
	}
	return 0
}
