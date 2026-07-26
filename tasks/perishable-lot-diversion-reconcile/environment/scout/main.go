package main

import (
	"encoding/csv"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
)

func countCSV(path string) (int, error) {
	f, err := os.Open(path)
	if err != nil {
		return 0, err
	}
	defer f.Close()
	rows, err := csv.NewReader(f).ReadAll()
	if err != nil {
		return 0, err
	}
	if len(rows) <= 1 {
		return 0, nil
	}
	return len(rows) - 1, nil
}

func main() {
	root := flag.String("root", "/app/data", "data root")
	flag.Parse()
	div, err := countCSV(filepath.Join(*root, "control", "diversions.csv"))
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	docks := []string{"dock_a.csv", "dock_b.csv", "dock_c.csv"}
	sensorRows := 0
	for _, name := range docks {
		n, err := countCSV(filepath.Join(*root, "sensors", name))
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		sensorRows += n
	}
	out := map[string]any{
		"diversion_rows": div,
		"sensor_rows":    sensorRows,
		"docks":          len(docks),
	}
	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	_ = enc.Encode(out)
}
