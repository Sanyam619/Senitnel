package main

import (
	"flag"
	"fmt"
	"os"

	"rly/internal/digest"
)

func main() {
	blobRoot := flag.String("blobs", "/data/blobs", "blob dir")
	label := flag.String("label", "", "blob label")
	flag.Parse()
	if *label == "" {
		fmt.Fprintln(os.Stderr, "missing --label")
		os.Exit(2)
	}
	sum, err := digest.FileHex(fmt.Sprintf("%s/%s.bin", *blobRoot, *label))
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	fmt.Println(sum)
}
