package trace

import (
	"crypto/sha256"
	"encoding/hex"
	"os"
)

func FileSHA256(path string) (string, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return "", err
	}
	sum := sha256.Sum256(raw)
	return hex.EncodeToString(sum[:]), nil
}

func CompareRoots(primaryPath, shadowPath string) (bool, string, string, error) {
	p, err := FileSHA256(primaryPath)
	if err != nil {
		return false, "", "", err
	}
	s, err := FileSHA256(shadowPath)
	if err != nil {
		return false, "", "", err
	}
	return p == s, p, s, nil
}
