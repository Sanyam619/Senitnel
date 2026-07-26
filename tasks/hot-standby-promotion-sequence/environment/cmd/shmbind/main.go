package main

import (
	"flag"
	"fmt"
	"os"
	"strconv"

	"lab/internal/shmio"
)

func main() {
	shmPath := flag.String("shm", "", "shm file path")
	saltStr := flag.String("salt", "", "salt value")
	flag.Parse()
	if *shmPath == "" || *saltStr == "" {
		fmt.Fprintln(os.Stderr, "usage: shmbind --shm PATH --salt N")
		os.Exit(2)
	}
	salt64, err := strconv.ParseUint(*saltStr, 10, 32)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if err := shmio.AlignFile(*shmPath, uint32(salt64)); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	fmt.Println("aligned")
}
