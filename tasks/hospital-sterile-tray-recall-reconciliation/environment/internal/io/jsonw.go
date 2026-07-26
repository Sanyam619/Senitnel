package io

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"csp.local/reconcile/internal/model"
)

func WriteLedger(path string, rows []model.LedgerRow) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	defer f.Close()
	for _, r := range rows {
		b, _ := json.Marshal(r)
		if _, err := fmt.Fprintf(f, "%s\n", b); err != nil {
			return err
		}
	}
	return nil
}

func WriteDisposition(path string, trays []model.TrayRow) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	payload := struct {
		Version int             `json:"version"`
		Trays   []model.TrayRow `json:"trays"`
	}{Version: 1, Trays: trays}
	b, err := json.MarshalIndent(payload, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, b, 0o644)
}
