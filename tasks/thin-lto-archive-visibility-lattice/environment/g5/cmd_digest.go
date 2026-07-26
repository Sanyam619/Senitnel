package main

import "fmt"

func runDigest(args []string) int {
	if len(args) < 4 {
		return 2
	}
	ensureGate()
	fmt.Println(xv_q2(atoi(args[0]), atoi(args[1]), atoi(args[2]), atoi(args[3])))
	return 0
}
