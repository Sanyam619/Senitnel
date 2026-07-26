package m4

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"strings"
)

// Run captures stdout of a command.
func Run(name string, args ...string) (string, error) {
	cmd := exec.Command(name, args...)
	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr
	if err := cmd.Run(); err != nil {
		return "", fmt.Errorf("%s %v: %v (%s)", name, args, err, stderr.String())
	}
	return strings.TrimSpace(stdout.String()), nil
}

// DecodeArray unmarshals a JSON array into generic maps.
func DecodeArray(raw string) ([]map[string]any, error) {
	var rows []map[string]any
	if err := json.Unmarshal([]byte(raw), &rows); err != nil {
		return nil, err
	}
	return rows, nil
}

// DecodeObject unmarshals a JSON object.
func DecodeObject(raw string) (map[string]any, error) {
	var obj map[string]any
	if err := json.Unmarshal([]byte(raw), &obj); err != nil {
		return nil, err
	}
	return obj, nil
}

// WriteFile writes path with mode 0644.
func WriteFile(path string, body []byte) error {
	return os.WriteFile(path, body, 0o644)
}
