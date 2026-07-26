package main

import (
	"flag"
	"fmt"
	"os"

	"lab/pkg/phase"
)

func main() {
	unified := flag.String("unified", "/data/lab/cgroup/unified", "unified root")
	slice := flag.String("slice", "app.slice", "slice name")
	flag.Parse()
	units := []string{"app-api.scope", "app-batch.scope", "app-worker.scope"}
	for _, unit := range units {
		if err := phase.LegacyRelay(*unified, *slice, unit, []string{"io", "memory"}); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	}
	fmt.Println("shadowlift complete")
}
