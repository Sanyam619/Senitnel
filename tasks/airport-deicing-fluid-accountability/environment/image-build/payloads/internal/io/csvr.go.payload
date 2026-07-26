package io

import (
	"bufio"
	"os"
	"strings"
)

func ReadCSV(path string) ([][]string, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	var rows [][]string
	scan := bufio.NewScanner(f)
	first := true
	for scan.Scan() {
		line := strings.TrimSpace(scan.Text())
		if line == "" {
			continue
		}
		if first {
			first = false
			continue
		}
		rows = append(rows, strings.Split(line, ","))
	}
	return rows, scan.Err()
}
