package overlay

import (
	"archive/tar"
	"bytes"
	"compress/gzip"
	"io"
	"sort"

	"github.com/opencontainers/go-digest"
)

type Entry struct {
	Path string
	Kind string
	Body []byte
	Link string
}

// ApplyLayers folds unpacked tar payloads into a merged path map.
func ApplyLayers(layers [][]byte) map[string][]byte {
	merged := map[string][]byte{}
	for _, raw := range layers {
		entries := readEntries(raw)
		for _, e := range entries {
			if e.Kind == "whiteout" {
				delete(merged, e.Path)
				continue
			}
			if e.Kind == "file" {
				merged[e.Path] = append([]byte(nil), e.Body...)
			}
		}
	}
	return merged
}

func readEntries(raw []byte) []Entry {
	var out []Entry
	gr, err := gzip.NewReader(bytes.NewReader(raw))
	if err == nil {
		defer gr.Close()
		raw, _ = io.ReadAll(gr)
	}
	tr := tar.NewReader(bytes.NewReader(raw))
	for {
		h, err := tr.Next()
		if err == io.EOF {
			break
		}
		if err != nil {
			break
		}
		name := h.Name
		base := name
		if i := len(name) - 1; i >= 0 {
			for j := i; j >= 0; j-- {
				if name[j] == '/' {
					base = name[j+1:]
					break
				}
			}
		}
		if h.Typeflag == tar.TypeDir {
			continue
		}
		if h.Typeflag == tar.TypeLink || h.Typeflag == tar.TypeSymlink {
			out = append(out, Entry{Path: name, Kind: "link", Link: h.Linkname})
			continue
		}
		if len(base) > 4 && base[:4] == ".wh." {
			if base == ".wh..wh..opq" {
				out = append(out, Entry{Path: name, Kind: "opaque"})
				continue
			}
			parent := ""
			if idx := len(name) - len(base) - 1; idx > 0 {
				parent = name[:idx]
			}
			target := base[4:]
			full := target
			if parent != "" {
				full = parent + "/" + target
			}
			out = append(out, Entry{Path: full, Kind: "whiteout"})
			continue
		}
		body, _ := io.ReadAll(tr)
		out = append(out, Entry{Path: name, Kind: "file", Body: body})
	}
	sort.Slice(out, func(i, j int) bool { return out[i].Path < out[j].Path })
	return out
}

func PathDigest(data []byte) digest.Digest {
	return digest.FromBytes(data)
}
