package main

import (
	"fmt"
	"os"
	"path/filepath"
)

func main() {
	root := "/var/lib/ingest"
	slots, _ := filepath.Glob(root + "/ring/*/slots/*")
	if len(slots) > 0 {
		fmt.Println("ActiveState=active")
		fmt.Println("slots=present")
		os.Exit(0)
	}
	fmt.Println("ActiveState=degraded")
	os.Exit(0)
}
