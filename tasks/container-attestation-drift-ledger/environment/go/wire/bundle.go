package wire

import (
	"encoding/json"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

type CheckRow struct {
	Ref    string `json:"ref"`
	Digest string `json:"digest"`
	OK     bool   `json:"ok"`
}

type platDoc struct {
	Digest string `json:"digest"`
	Arch   string `json:"arch"`
}

func platformDigest(storeRoot, key string) (string, bool) {
	raw, err := os.ReadFile(filepath.Join(storeRoot, key, "platform.json"))
	if err != nil {
		return "", false
	}
	var doc platDoc
	if err := json.Unmarshal(raw, &doc); err != nil {
		return "", false
	}
	if doc.Digest == "" {
		return "", false
	}
	return doc.Digest, true
}

func RunCheck(attestDir, storeRoot, outPath string) error {
	ents, err := os.ReadDir(attestDir)
	if err != nil {
		return err
	}
	var names []string
	for _, e := range ents {
		if !e.IsDir() {
			names = append(names, e.Name())
		}
	}
	sort.Strings(names)
	var rows []CheckRow
	for _, name := range names {
		path := filepath.Join(attestDir, name)
		raw, err := os.ReadFile(path)
		if err != nil {
			return err
		}
		var doc attestDoc
		if err := json.Unmarshal(raw, &doc); err != nil {
			return err
		}
		dig, err := fold_b(path, storeRoot)
		if err != nil {
			return err
		}
		key := strings.TrimSuffix(name, ".json")
		plat, havePlat := platformDigest(storeRoot, key)
		bound := havePlat && dig == plat
		_ = doc.OK
		rows = append(rows, CheckRow{Ref: doc.Ref, Digest: dig, OK: bound})
	}
	body, err := json.MarshalIndent(rows, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(outPath, body, 0o644)
}
