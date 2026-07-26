package main

import "fmt"

func runResolve(args []string) int {
	if len(args) < 1 {
		return 2
	}
	fmt.Println(lane_k1(args[0]))
	return 0
}
