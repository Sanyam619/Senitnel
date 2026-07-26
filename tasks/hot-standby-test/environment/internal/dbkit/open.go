package dbkit

import (
	"fmt"
	"os"
	"os/exec"
	"strconv"
	"strings"
)

func OpenPath(path string) error {
	if _, err := os.Stat(path); err != nil {
		return err
	}
	return nil
}

func UserVersion(path string) (int, error) {
	out, err := exec.Command("sqlite3", path, "PRAGMA user_version;").Output()
	if err != nil {
		return 0, err
	}
	text := strings.TrimSpace(string(out))
	return strconv.Atoi(text)
}

func SchemaVersion(path string) (int, error) {
	out, err := exec.Command("sqlite3", path, "PRAGMA schema_version;").Output()
	if err != nil {
		return 0, err
	}
	text := strings.TrimSpace(string(out))
	return strconv.Atoi(text)
}

func QuerySingleString(path, query string) (string, error) {
	out, err := exec.Command("sqlite3", path, query).Output()
	if err != nil {
		return "", fmt.Errorf("query failed: %w", err)
	}
	return strings.TrimSpace(string(out)), nil
}
