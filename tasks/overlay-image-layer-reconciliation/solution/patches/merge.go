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

// ApplyLayers folds unpacked tar payloads bottom-to-top across marker rows.
func ApplyLayers(layers [][]byte) map[string][]byte {
	merged := map[string][]byte{}
	for _, raw := range layers {
		entries := readEntries(raw)
		var opaqueDirs []string
		var whiteouts []string
		var files []Entry
		var links []Entry
		for _, e := range entries {
			switch e.Kind {
			case "opaque":
				opaqueDirs = append(opaqueDirs, parentDir(e.Path))
			case "whiteout":
				whiteouts = append(whiteouts, e.Path)
			case "file":
				files = append(files, e)
			case "link":
				links = append(links, e)
			}
		}
		for _, dir := range opaqueDirs {
			prefix := dir + "/"
			for k := range merged {
				if dir == "" {
					if !containsSlash(k) {
						delete(merged, k)
					}
				} else if k == dir || len(k) > len(prefix) && k[:len(prefix)] == prefix {
					delete(merged, k)
				}
			}
		}
		for _, p := range whiteouts {
			delete(merged, p)
		}
		for _, e := range files {
			merged[e.Path] = append([]byte(nil), e.Body...)
		}
		for _, e := range links {
			if body, ok := merged[e.Link]; ok {
				merged[e.Path] = append([]byte(nil), body...)
			}
		}
	}
	return merged
}

func parentDir(p string) string {
	if i := len(p) - 1; i >= 0 {
		for j := i; j >= 0; j-- {
			if p[j] == '/' {
				return p[:j]
			}
		}
	}
	return ""
}

func containsSlash(s string) bool {
	for i := 0; i < len(s); i++ {
		if s[i] == '/' {
			return true
		}
	}
	return false
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
