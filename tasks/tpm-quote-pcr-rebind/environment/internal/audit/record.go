package audit

import (
	"encoding/json"
	"os"
	"time"
)

type Entry struct {
	Tool   string `json:"tool"`
	Action string `json:"action"`
	When   string `json:"when"`
}

type Log struct {
	Version int     `json:"version"`
	Steps   []Entry `json:"steps"`
}

func Append(path, tool, action string) error {
	var doc Log
	if raw, err := os.ReadFile(path); err == nil {
		_ = json.Unmarshal(raw, &doc)
	}
	if doc.Version == 0 {
		doc.Version = 1
	}
	doc.Steps = append(doc.Steps, Entry{
		Tool:   tool,
		Action: action,
		When:   time.Now().UTC().Format(time.RFC3339),
	})
	raw, err := json.MarshalIndent(doc, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, raw, 0o644)
}
