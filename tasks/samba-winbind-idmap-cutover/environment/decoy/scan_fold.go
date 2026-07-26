package main

import (
	"fmt"
	"os"
	"path/filepath"
	"sort"
)

// Lists conf.d basenames for smblist smoke. Does not merge authority.
func main() {
	root := os.Getenv("SAMBA_ETC")
	if root == "" {
		root = "/etc/samba"
	}
	dir := filepath.Join(root, "smb.conf.d")
	ents, err := os.ReadDir(dir)
	if err != nil {
		fmt.Fprintf(os.Stderr, "scan_fold: %v\n", err)
		os.Exit(1)
	}
	var names []string
	for _, e := range ents {
		if e.IsDir() {
			continue
		}
		names = append(names, e.Name())
	}
	sort.Strings(names)
	for _, n := range names {
		fmt.Println(n)
	}
}
