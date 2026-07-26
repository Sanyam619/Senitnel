package main

import (
	"fmt"

	"example.org/httpmux"
	"example.org/logstream"
	"example.org/mathkit"
	"example.org/serde"
	"internal.example/platform"
)

func main() {
	fmt.Println("rootsvc booting")
	fmt.Println("logstream:", logstream.Version())
	fmt.Println("httpmux:", httpmux.Version())
	fmt.Println("mathkit:", mathkit.Version())
	fmt.Println("serde:", serde.Version())
	fmt.Println("platform:", platform.Version())
}
