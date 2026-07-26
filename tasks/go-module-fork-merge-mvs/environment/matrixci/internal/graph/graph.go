package graph

import (
	"bufio"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

// ModFile represents a parsed go.mod-like file (subset relevant to matrixci).
type ModFile struct {
	Module    string
	Go        string
	Toolchain string
	Require   []Require
	Replace   []Replace
	Exclude   []Exclude
	Retract   []Retract
}

type Require struct {
	Path    string
	Version string
}

type Replace struct {
	Path      string
	OldVer    string
	NewPath   string
	NewVer    string
}

type Exclude struct {
	Path    string
	Version string
}

type Retract struct {
	Low  string
	High string
}

// ProxyModule describes what the local module proxy knows about a module path.
type ProxyModule struct {
	Path         string
	Versions     []string
	LatestMod    *ModFile
	MinGoDirective map[string]string // per-version "go" directive from that version's .mod
}

// LoadModFile reads a single go.mod-style file.
func LoadModFile(path string) (*ModFile, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	return parseModReader(f)
}

func parseModReader(r io.Reader) (*ModFile, error) {
	m := &ModFile{}
	sc := bufio.NewScanner(r)
	inRequire := false
	inReplace := false
	inExclude := false
	inRetract := false
	for sc.Scan() {
		line := stripComment(sc.Text())
		trim := strings.TrimSpace(line)
		if trim == "" {
			continue
		}
		if inRequire || inReplace || inExclude || inRetract {
			if trim == ")" {
				inRequire, inReplace, inExclude, inRetract = false, false, false, false
				continue
			}
			if inRequire {
				addRequire(m, trim)
			} else if inReplace {
				addReplace(m, trim)
			} else if inExclude {
				addExclude(m, trim)
			} else if inRetract {
				addRetract(m, trim)
			}
			continue
		}
		switch {
		case strings.HasPrefix(trim, "module "):
			m.Module = strings.TrimSpace(strings.TrimPrefix(trim, "module "))
		case strings.HasPrefix(trim, "go "):
			m.Go = strings.TrimSpace(strings.TrimPrefix(trim, "go "))
		case strings.HasPrefix(trim, "toolchain "):
			m.Toolchain = strings.TrimSpace(strings.TrimPrefix(trim, "toolchain "))
		case trim == "require (":
			inRequire = true
		case strings.HasPrefix(trim, "require "):
			addRequire(m, strings.TrimPrefix(trim, "require "))
		case trim == "replace (":
			inReplace = true
		case strings.HasPrefix(trim, "replace "):
			addReplace(m, strings.TrimPrefix(trim, "replace "))
		case trim == "exclude (":
			inExclude = true
		case strings.HasPrefix(trim, "exclude "):
			addExclude(m, strings.TrimPrefix(trim, "exclude "))
		case trim == "retract (":
			inRetract = true
		case strings.HasPrefix(trim, "retract "):
			addRetract(m, strings.TrimPrefix(trim, "retract "))
		}
	}
	return m, sc.Err()
}

func stripComment(s string) string {
	if i := strings.Index(s, "//"); i >= 0 {
		return s[:i]
	}
	return s
}

func addRequire(m *ModFile, body string) {
	body = strings.TrimSuffix(body, ")")
	parts := strings.Fields(body)
	if len(parts) < 2 {
		return
	}
	m.Require = append(m.Require, Require{Path: parts[0], Version: parts[1]})
}

func addReplace(m *ModFile, body string) {
	parts := strings.Fields(body)
	// Forms:
	//   path => newpath ver
	//   path ver => newpath ver
	//   path => path ver  (in-tree)
	arrow := indexOf(parts, "=>")
	if arrow < 0 {
		return
	}
	left := parts[:arrow]
	right := parts[arrow+1:]
	rep := Replace{}
	rep.Path = left[0]
	if len(left) > 1 {
		rep.OldVer = left[1]
	}
	if len(right) == 0 {
		return
	}
	rep.NewPath = right[0]
	if len(right) > 1 {
		rep.NewVer = right[1]
	}
	m.Replace = append(m.Replace, rep)
}

func addExclude(m *ModFile, body string) {
	parts := strings.Fields(body)
	if len(parts) < 2 {
		return
	}
	m.Exclude = append(m.Exclude, Exclude{Path: parts[0], Version: parts[1]})
}

func addRetract(m *ModFile, body string) {
	body = strings.TrimSpace(body)
	if strings.HasPrefix(body, "[") {
		// Range form: [vX, vY]
		trimmed := strings.TrimSuffix(strings.TrimPrefix(body, "["), "]")
		parts := strings.Split(trimmed, ",")
		if len(parts) == 2 {
			m.Retract = append(m.Retract, Retract{
				Low:  strings.TrimSpace(parts[0]),
				High: strings.TrimSpace(parts[1]),
			})
		}
		return
	}
	// Single-version form.
	parts := strings.Fields(body)
	if len(parts) >= 1 {
		m.Retract = append(m.Retract, Retract{Low: parts[0], High: parts[0]})
	}
}

func indexOf(a []string, s string) int {
	for i, v := range a {
		if v == s {
			return i
		}
	}
	return -1
}

// LoadProxy walks the proxy root and loads metadata for each module path.
// The proxy layout mirrors Go's file-based proxy:
//
//	proxy/<module-path>/@v/<version>.info
//	proxy/<module-path>/@v/<version>.mod
//	proxy/<module-path>/@v/list
func LoadProxy(root string) (map[string]*ProxyModule, string, error) {
	out := map[string]*ProxyModule{}
	// Collect all @v directories.
	var vDirs []string
	err := filepath.Walk(root, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		if info.IsDir() && info.Name() == "@v" {
			vDirs = append(vDirs, path)
		}
		return nil
	})
	if err != nil {
		return nil, "", err
	}
	sort.Strings(vDirs)
	for _, vd := range vDirs {
		rel, _ := filepath.Rel(root, filepath.Dir(vd))
		pathModule := filepath.ToSlash(rel)
		pm := &ProxyModule{Path: pathModule, MinGoDirective: map[string]string{}}
		listPath := filepath.Join(vd, "list")
		if lb, err := os.ReadFile(listPath); err == nil {
			for _, ln := range strings.Split(string(lb), "\n") {
				ln = strings.TrimSpace(ln)
				if ln != "" {
					pm.Versions = append(pm.Versions, ln)
				}
			}
		}
		// Parse per-version mod files.
		for _, v := range pm.Versions {
			modP := filepath.Join(vd, v+".mod")
			mf, err := LoadModFile(modP)
			if err != nil {
				return nil, "", fmt.Errorf("proxy %s@%s: %w", pathModule, v, err)
			}
			pm.MinGoDirective[v] = mf.Go
		}
		// Latest version's mod file carries retract information.
		if len(pm.Versions) > 0 {
			latest := pm.Versions[len(pm.Versions)-1]
			mf, err := LoadModFile(filepath.Join(vd, latest+".mod"))
			if err == nil {
				pm.LatestMod = mf
			}
		}
		out[pathModule] = pm
	}
	return out, digestProxy(root, vDirs), nil
}

func digestProxy(root string, vDirs []string) string {
	h := sha256.New()
	for _, vd := range vDirs {
		rel, _ := filepath.Rel(root, vd)
		fmt.Fprintln(h, filepath.ToSlash(rel))
		entries, _ := os.ReadDir(vd)
		names := make([]string, 0, len(entries))
		for _, e := range entries {
			names = append(names, e.Name())
		}
		sort.Strings(names)
		for _, n := range names {
			b, err := os.ReadFile(filepath.Join(vd, n))
			if err == nil {
				fmt.Fprintln(h, n)
				h.Write(b)
			}
		}
	}
	return hex.EncodeToString(h.Sum(nil))
}

// HasToolsBuildConstraint reports whether the tools file guards its imports
// behind a build constraint that keeps them out of the default vendor set.
func HasToolsBuildConstraint(path string) (bool, error) {
	f, err := os.Open(path)
	if err != nil {
		if os.IsNotExist(err) {
			return true, nil
		}
		return false, err
	}
	defer f.Close()
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "" {
			continue
		}
		if strings.HasPrefix(line, "//go:build") {
			// Any build constraint that doesn't unconditionally include is enough.
			body := strings.TrimSpace(strings.TrimPrefix(line, "//go:build"))
			if body != "" && body != "!ignore" {
				return true, nil
			}
		}
		if strings.HasPrefix(line, "// +build") {
			return true, nil
		}
		if strings.HasPrefix(line, "package ") {
			return false, nil
		}
	}
	return false, sc.Err()
}
