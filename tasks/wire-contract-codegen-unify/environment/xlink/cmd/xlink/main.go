package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"lab.local/xlink/internal/m4"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: xlink <report|probe-binary|probe-json> ...")
		os.Exit(2)
	}
	switch os.Args[1] {
	case "report":
		out := "/output/wire-unify.json"
		for i := 2; i < len(os.Args); i++ {
			if os.Args[i] == "--out" && i+1 < len(os.Args) {
				out = os.Args[i+1]
				i++
			}
		}
		if err := runReport(out); err != nil {
			fmt.Fprintf(os.Stderr, "xlink report: %v\n", err)
			os.Exit(1)
		}
	case "probe-binary":
		st, err := probeStatus("binary")
		if err != nil {
			fmt.Fprintf(os.Stderr, "xlink probe-binary: %v\n", err)
			os.Exit(1)
		}
		fmt.Printf("{\"status\":%q}\n", st)
	case "probe-json":
		st, err := probeStatus("json")
		if err != nil {
			fmt.Fprintf(os.Stderr, "xlink probe-json: %v\n", err)
			os.Exit(1)
		}
		fmt.Printf("{\"status\":%q}\n", st)
	default:
		fmt.Fprintf(os.Stderr, "unknown subcommand %q\n", os.Args[1])
		os.Exit(2)
	}
}

func runReport(outPath string) error {
	goRaw, err := m4.Run("/app/bin/foldctl")
	if err != nil {
		return err
	}
	rustRaw, err := m4.Run("/app/bin/sievectl")
	if err != nil {
		return err
	}
	javaRaw, err := m4.Run("java", "-cp", "/app/jvx/classes", "org.lab.p7.LaneMain")
	if err != nil {
		return err
	}

	goRows, err := m4.DecodeArray(goRaw)
	if err != nil {
		return fmt.Errorf("go rows: %w", err)
	}
	rustRows, err := m4.DecodeArray(rustRaw)
	if err != nil {
		return fmt.Errorf("rust rows: %w", err)
	}
	javaObj, err := m4.DecodeObject(javaRaw)
	if err != nil {
		return fmt.Errorf("java obj: %w", err)
	}
	javaRowsAny, ok := javaObj["rows"].([]any)
	if !ok {
		return fmt.Errorf("java rows missing")
	}
	javaRows := make([]map[string]any, 0, len(javaRowsAny))
	for _, item := range javaRowsAny {
		m, ok := item.(map[string]any)
		if !ok {
			return fmt.Errorf("java row type")
		}
		javaRows = append(javaRows, m)
	}

	digest, _ := javaObj["contract_digest"].(string)
	binSt, _ := javaObj["binary_status"].(string)
	jsonSt, _ := javaObj["json_status"].(string)

	report := map[string]any{
		"schema_version":   1,
		"contract_digest":  digest,
		"go_rows":          goRows,
		"rust_rows":        rustRows,
		"java_rows":        javaRows,
		"binary_probe":     map[string]any{"status": binSt},
		"json_probe":       map[string]any{"status": jsonSt},
	}
	body, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		return err
	}
	if err := os.MkdirAll(filepath.Dir(outPath), 0o755); err != nil {
		return err
	}
	return m4.WriteFile(outPath, append(body, '\n'))
}

func probeStatus(kind string) (string, error) {
	javaRaw, err := m4.Run("java", "-cp", "/app/jvx/classes", "org.lab.p7.LaneMain")
	if err != nil {
		return "", err
	}
	obj, err := m4.DecodeObject(javaRaw)
	if err != nil {
		return "", err
	}
	key := "binary_status"
	if kind == "json" {
		key = "json_status"
	}
	st, _ := obj[key].(string)
	if st == "" {
		st = "fail"
	}
	return st, nil
}
