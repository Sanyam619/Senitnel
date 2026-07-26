package main

import (
	"archive/tar"
	"bytes"
	"compress/gzip"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"sort"

	"github.com/opencontainers/go-digest"
)

func main() {
	root := flag.String("root", "/data/images", "bundle root")
	id := flag.String("id", "", "bundle id")
	flag.Parse()
	if *id == "" {
		fmt.Fprintln(os.Stderr, "missing id")
		os.Exit(1)
	}
	base := filepath.Join(*root, *id)
	mb, _ := os.ReadFile(filepath.Join(base, "index.json"))
	var man struct {
		Layers []struct {
			Digest digest.Digest `json:"digest"`
		} `json:"layers"`
	}
	_ = json.Unmarshal(mb, &man)
	merged := map[string][]byte{}
	for _, layer := range man.Layers {
		path := filepath.Join(base, "blobs", "sha256", layer.Digest.Encoded())
		b, _ := os.ReadFile(path)
		gr, _ := gzip.NewReader(bytes.NewReader(b))
		raw, _ := io.ReadAll(gr)
		gr.Close()
		tr := tar.NewReader(bytes.NewReader(raw))
		for {
			h, err := tr.Next()
			if err == io.EOF {
				break
			}
			if h.Typeflag != tar.TypeReg {
				continue
			}
			body, _ := io.ReadAll(tr)
			merged[h.Name] = body
		}
	}
	keys := make([]string, 0, len(merged))
	for k := range merged {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	for _, k := range keys {
		fmt.Printf("%s\t%d\n", k, len(merged[k]))
	}
}
