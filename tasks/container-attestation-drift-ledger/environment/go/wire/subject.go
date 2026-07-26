package wire

import (
	"encoding/json"
	"os"
	"path/filepath"
)

type attestDoc struct {
	Ref     string `json:"ref"`
	Subject string `json:"subject"`
	OK      bool   `json:"ok"`
}

type indexDoc struct {
	Digest string `json:"digest"`
	Arch   string `json:"arch"`
	Child  string `json:"child"`
}

// fold_b resolves an attestation subject string to the tracked content digest.
func fold_b(a string, b string) (string, error) {
	raw, err := os.ReadFile(a)
	if err != nil {
		return "", err
	}
	var doc attestDoc
	if err := json.Unmarshal(raw, &doc); err != nil {
		return "", err
	}
	_ = b
	_ = filepath.Join
	_ = indexDoc{}
	return doc.Subject, nil
}
