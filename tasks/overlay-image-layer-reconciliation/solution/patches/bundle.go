package descript

import (
	"bytes"
	"compress/gzip"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
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

// LoadMeta reads descriptor JSON and retains only rows tied to the chain file.
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
	wireSet := map[digest.Digest]struct{}{}
	for _, wid := range wire.RootFS.DiffIDs {
		wireSet[wid] = struct{}{}
	}
	order := make([]digest.Digest, 0, len(man.Layers))
	for _, layer := range man.Layers {
		payload, err := os.ReadFile(filepath.Join(base, "blobs", "sha256", layer.Digest.Encoded()))
		if err != nil {
			continue
		}
		raw, err := gunzipLocal(payload)
		if err != nil {
			continue
		}
		h := sha256.Sum256(raw)
		diff := digest.Digest("sha256:" + hex.EncodeToString(h[:]))
		if _, ok := wireSet[diff]; ok {
			order = append(order, layer.Digest)
		}
	}
	if len(order) == 0 {
		return Bundle{}, fmt.Errorf("empty manifest for %s", id)
	}
	return Bundle{ID: id, Manifest: order, WireIDs: wire.RootFS.DiffIDs}, nil
}

func gunzipLocal(b []byte) ([]byte, error) {
	gr, err := gzip.NewReader(bytes.NewReader(b))
	if err != nil {
		return nil, err
	}
	defer gr.Close()
	return io.ReadAll(gr)
}
