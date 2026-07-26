package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strconv"

	"lab.local/hydro_lane/internal/k3"
	"lab.local/hydro_lane/internal/m7"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: window <head|aggregate>")
		os.Exit(2)
	}
	dataRoot := "/app/data"
	configDir := "/app/config/l7"
	switch os.Args[1] {
	case "head":
		gen, err := m7.ResolveHead(filepath.Join(dataRoot, "manifests"), configDir)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		fmt.Println(gen)
	case "aggregate":
		var channel string
		var ts int64
		for i := 2; i < len(os.Args); i++ {
			switch os.Args[i] {
			case "--ks":
				if i+1 >= len(os.Args) {
					os.Exit(2)
				}
				channel = os.Args[i+1]
				i++
			case "--ts":
				if i+1 >= len(os.Args) {
					os.Exit(2)
				}
				v, err := strconv.ParseInt(os.Args[i+1], 10, 64)
				if err != nil {
					os.Exit(2)
				}
				ts = v
				i++
			}
		}
		if channel == "" || ts == 0 {
			os.Exit(2)
		}
		count, sum, err := k3.MergedAggregate(dataRoot, channel, ts)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		out, _ := json.Marshal(map[string]any{"count": count, "sum_ts": sum})
		fmt.Println(string(out))
	default:
		os.Exit(2)
	}
}
