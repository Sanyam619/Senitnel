package main

import "fmt"

func runMembers(args []string) int {
	if len(args) < 3 {
		return 2
	}
	a := atoi(args[0])
	b := atoi(args[1])
	m := atoi(args[2])
	fmt.Println(cg_n5(a, b, m))
	return 0
}
