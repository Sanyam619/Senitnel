package main

import (
	"fmt"
	"os"

	"meshqx/internal"
)

func main() {
	root := "/app"
	if v := os.Getenv("APP_ROOT"); v != "" {
		root = v
	}
	if len(os.Args) > 1 && os.Args[1] == "surface" {
		for _, req := range os.Args[2:] {
			fmt.Printf("%s %s\n", req, internal.SurfLine(req))
		}
		return
	}
	if err := internal.RunAll(root); err != nil {
		fmt.Fprintf(os.Stderr, "%v\n", err)
		os.Exit(1)
	}
}
