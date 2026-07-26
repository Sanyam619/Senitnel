package descript

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/opencontainers/go-digest"
)

type Descriptor struct {
	Digest digest.Digest `json:"digest"`
	Size   int64         `json:"size"`
}

type WireConfig struct {
	RootFS struct {
		Type     string           `json:"type"`
		DiffIDs  []digest.Digest  `json:"diff_ids"`
	} `json:"rootfs"`
}

type Bundle struct {
	ID       string
	Manifest []digest.Digest
	WireIDs  []digest.Digest
}

// LoadMeta reads descriptor JSON for a bundle tree.
func LoadMeta(root, id string) (Bundle, error) {
	base := filepath.Join(root, id)
	var man struct {
		Layers []Descriptor `json:"layers"`
	}
	mb, err := os.ReadFile(filepath.Join(base, "index.json"))
	if err != nil {
		return Bundle{}, err
	}
	if err := json.Unmarshal(mb, &man); err != nil {
		return Bundle{}, err
	}
	cb, err := os.ReadFile(filepath.Join(base, "wire.json"))
	if err != nil {
		return Bundle{}, err
	}
	var wire WireConfig
	if err := json.Unmarshal(cb, &wire); err != nil {
		return Bundle{}, err
	}
	order := make([]digest.Digest, 0, len(man.Layers))
	for _, layer := range man.Layers {
		order = append(order, layer.Digest)
	}
	if len(order) == 0 {
		return Bundle{}, fmt.Errorf("empty manifest for %s", id)
	}
	return Bundle{ID: id, Manifest: order, WireIDs: wire.RootFS.DiffIDs}, nil
}
