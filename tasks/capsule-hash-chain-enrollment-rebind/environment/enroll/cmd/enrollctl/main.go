package main

import (
	"fmt"
	"os"

	"capsule.local/enroll/internal"
)

func main() {
	if err := internal.Enroll(); err != nil {
		fmt.Fprintln(os.Stderr, "enrollctl:", err)
		os.Exit(1)
	}
}
