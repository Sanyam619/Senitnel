package digest

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"os"
	"path/filepath"
	"sort"
)

type BlobRow struct {
	Label  string `json:"label"`
	SHA256 string `json:"sha256"`
}

func FileHex(path string) (string, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return "", err
	}
	sum := sha256.Sum256(raw)
	return hex.EncodeToString(sum[:]), nil
}

func Collect(dir string, labels []string) ([]BlobRow, error) {
	rows := make([]BlobRow, 0, len(labels))
	for _, label := range labels {
		path := filepath.Join(dir, label+".bin")
		sum, err := FileHex(path)
		if err != nil {
			return nil, fmt.Errorf("%s: %w", label, err)
		}
		rows = append(rows, BlobRow{Label: label, SHA256: sum})
	}
	sort.Slice(rows, func(i, j int) bool { return rows[i].Label < rows[j].Label })
	return rows, nil
}

func Combined(rows []BlobRow) string {
	h := sha256.New()
	for _, row := range rows {
		h.Write([]byte(row.Label))
		h.Write([]byte(row.SHA256))
	}
	return hex.EncodeToString(h.Sum(nil))
}
