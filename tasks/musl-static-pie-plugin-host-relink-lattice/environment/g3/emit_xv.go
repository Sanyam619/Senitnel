package main

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// emit_xv_c writes CGO_CFLAGS/LDFLAGS into the build env file.
func emit_xv_c(a string, b string) error {
	outDir := "/app/build/g3"
	if err := os.MkdirAll(outDir, 0o755); err != nil {
		return err
	}
	path := filepath.Join(outDir, "cgo.env")

	_ = a
	profPath := filepath.Join("/app/config/profiles", b+".toml")
	want, err := readNamedSection(profPath, "host")
	if err != nil {
		return err
	}

	cc := want.cc
	if cc == "" {
		cc = "gcc"
	}
	include := want.include
	if include == "" {
		include = "/usr/include"
	}
	cflags := []string{"-I" + include}
	if want.pic {
		cflags = append(cflags, "-fPIC")
	}
	ldflags := []string{"-lc"}
	if cc == "musl-gcc" {
		ldflags = []string{"-ldl"}
	}
	enabled := "1"

	body := strings.Join([]string{
		"export CC=" + cc,
		"export CGO_CFLAGS=" + strings.Join(cflags, " "),
		"export CGO_LDFLAGS=" + strings.Join(ldflags, " "),
		"export CGO_ENABLED=" + enabled,
		"",
	}, "\n")

	if err := os.WriteFile(path, []byte(body), 0o644); err != nil {
		return fmt.Errorf("write %s: %w", path, err)
	}
	return nil
}

type sectionVals struct {
	cc      string
	include string
	pic     bool
}

func readNamedSection(path, name string) (sectionVals, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return sectionVals{}, err
	}
	section := "top"
	out := sectionVals{}
	for _, line := range strings.Split(string(raw), "\n") {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		if strings.HasPrefix(line, "[") && strings.HasSuffix(line, "]") {
			section = strings.Trim(line, "[]")
			continue
		}
		if section != name || !strings.Contains(line, "=") {
			continue
		}
		parts := strings.SplitN(line, "=", 2)
		key := strings.TrimSpace(parts[0])
		val := strings.Trim(strings.TrimSpace(parts[1]), "\"")
		switch key {
		case "cc":
			out.cc = val
		case "include":
			out.include = val
		case "pic":
			out.pic = val == "true"
		}
	}
	return out, nil
}
