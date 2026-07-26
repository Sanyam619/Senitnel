package main

import (
	"flag"
	"fmt"
	"os"
)

func main() {
	primaryWal := flag.String("primary-wal", "/data/primary/source.db-wal", "upstream wal path")
	replicaWal := flag.String("replica-wal", "/data/standby/replica.db-wal", "replica wal path")
	flag.Parse()
	pi, err := os.Stat(*primaryWal)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	ri, err := os.Stat(*replicaWal)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if pi.Size() == ri.Size() {
		fmt.Println("GREEN")
		os.Exit(0)
	}
	fmt.Println("RED")
	os.Exit(1)
}
