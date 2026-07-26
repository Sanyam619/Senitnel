package main

import (
	"fmt"
	"os"

	"meshlab/lane"
	"meshlab/roll"
	"meshlab/seat"
)

func main() {
	if err := lane.Apply(); err != nil {
		fmt.Fprintf(os.Stderr, "lane: %v\n", err)
		os.Exit(1)
	}
	if err := seat.Apply(); err != nil {
		fmt.Fprintf(os.Stderr, "seat: %v\n", err)
		os.Exit(1)
	}
	if err := roll.Apply(); err != nil {
		fmt.Fprintf(os.Stderr, "roll: %v\n", err)
		os.Exit(1)
	}
	fmt.Println("cutover drivers: ok")
}
