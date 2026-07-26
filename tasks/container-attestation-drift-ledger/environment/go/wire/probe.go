package wire

import (
	"encoding/json"
	"fmt"
	"os"
)

// DumpHeader prints attestation header fields for diagnostics; does not resolve subjects.
func DumpHeader(path string) error {
	raw, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	var doc map[string]any
	if err := json.Unmarshal(raw, &doc); err != nil {
		return err
	}
	ref, _ := doc["ref"].(string)
	ok, _ := doc["ok"].(bool)
	fmt.Printf("OK header ref=%s ok=%v\n", ref, ok)
	return nil
}
