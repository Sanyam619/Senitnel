package main

import (
	"fmt"
	"os"
)

func writeFlags(path string, members int) error {
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	defer f.Close()
	_, err = fmt.Fprintf(f, "ARCHIVE_MEMBERS=%d\n", members)
	return err
}
