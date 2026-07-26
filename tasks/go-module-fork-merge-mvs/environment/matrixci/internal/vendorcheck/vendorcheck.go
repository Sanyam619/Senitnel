package vendorcheck

import (
	"bufio"
	"fmt"
	"os"
	"sort"
	"strings"

	"internal.example/matrixci/internal/graph"
)

// VendorEntry is one `# path version` entry parsed from modules.txt,
// plus the `## explicit; go X.Y` metadata attached to it (if any).
type VendorEntry struct {
	Path        string
	Version     string
	Replaced    string // "" or replacement path
	ReplacedVer string
	GoDirective string // "" or the "X.Y" value from `## explicit; go X.Y`
}

// LoadModulesTxt reads a `vendor/modules.txt` file into a set of entries and
// returns a list of paths where the version listed contradicts what the
// module's own `.mod` published (missing `+incompatible` suffix, or the
// `## explicit; go X.Y` line disagreeing with the effective module's own
// `go` directive from the proxy `.mod`).
func LoadModulesTxt(path string, proxy map[string]*graph.ProxyModule) (map[string]VendorEntry, []string, error) {
	entries := map[string]VendorEntry{}
	f, err := os.Open(path)
	if err != nil {
		return nil, nil, err
	}
	defer f.Close()
	sc := bufio.NewScanner(f)
	var current *VendorEntry
	for sc.Scan() {
		line := sc.Text()
		if strings.HasPrefix(line, "# ") {
			body := strings.TrimSpace(strings.TrimPrefix(line, "#"))
			e := VendorEntry{}
			// Forms:
			//   # path version
			//   # path version => newpath newver
			if arrow := strings.Index(body, "=>"); arrow >= 0 {
				left := strings.Fields(strings.TrimSpace(body[:arrow]))
				right := strings.Fields(strings.TrimSpace(body[arrow+2:]))
				if len(left) >= 2 {
					e.Path = left[0]
					e.Version = left[1]
				}
				if len(right) >= 2 {
					e.Replaced = right[0]
					e.ReplacedVer = right[1]
				}
			} else {
				parts := strings.Fields(body)
				if len(parts) < 2 {
					current = nil
					continue
				}
				e.Path = parts[0]
				e.Version = parts[1]
			}
			entries[e.Path] = e
			// Track the entry we just added so the next `## explicit; go X.Y`
			// line can be attached to it.
			ref := entries[e.Path]
			current = &ref
			continue
		}
		if strings.HasPrefix(line, "## ") && current != nil {
			body := strings.TrimSpace(strings.TrimPrefix(line, "##"))
			// Format observed in Go's own vendor/modules.txt:
			//   ## explicit; go 1.20
			// The token following the "go" keyword is captured verbatim.
			for _, seg := range strings.Split(body, ";") {
				seg = strings.TrimSpace(seg)
				if strings.HasPrefix(seg, "go ") {
					gv := strings.TrimSpace(strings.TrimPrefix(seg, "go "))
					if gv != "" {
						updated := entries[current.Path]
						updated.GoDirective = gv
						entries[current.Path] = updated
					}
				}
			}
			continue
		}
	}
	// Drift check: `+incompatible` tag mismatch and go-directive mismatch.
	var drift []string
	for path, e := range entries {
		effective := e.Path
		effectiveVer := e.Version
		if e.Replaced != "" {
			effective = e.Replaced
			effectiveVer = e.ReplacedVer
		}
		pm := proxy[effective]
		if pm == nil {
			continue
		}
		// +incompatible tag drift.
		bareSelected := trimIncompatibleSuffix(effectiveVer)
		for _, v := range pm.Versions {
			if strings.HasSuffix(v, "+incompatible") && trimIncompatibleSuffix(v) == bareSelected {
				if !strings.HasSuffix(effectiveVer, "+incompatible") {
					drift = append(drift, fmt.Sprintf("%s: modules.txt has %s, proxy publishes %s", path, effectiveVer, v))
				}
			}
		}
		// go-directive parity: the `## explicit; go X.Y` must match the
		// effective module's own `go` directive from the proxy `.mod`.
		if e.GoDirective != "" {
			proxyGo := pm.MinGoDirective[effectiveVer]
			if proxyGo != "" && proxyGo != e.GoDirective {
				drift = append(drift, fmt.Sprintf("%s: modules.txt says go %s, proxy .mod for %s@%s says go %s", path, e.GoDirective, effective, effectiveVer, proxyGo))
			}
		}
	}
	sort.Strings(drift)
	return entries, drift, sc.Err()
}

// VerifyAgainstSelection checks that the vendor/modules.txt entries match the
// MVS selection and that the referenced versions exist in the proxy.
func VerifyAgainstSelection(sel map[string]string, entries map[string]VendorEntry, proxy map[string]*graph.ProxyModule) (bool, []string) {
	var diag []string
	for path, ver := range sel {
		if strings.HasPrefix(path, "internal.example/") {
			// Internal modules are always resolved from source in this monorepo;
			// they don't need vendor entries.
			continue
		}
		e, ok := entries[path]
		if !ok {
			diag = append(diag, fmt.Sprintf("%s missing from vendor/modules.txt", path))
			continue
		}
		effVer := ver
		effPath := path
		if e.Replaced != "" {
			effPath = e.Replaced
			effVer = e.ReplacedVer
		}
		if e.Version != ver && e.Replaced == "" {
			diag = append(diag, fmt.Sprintf("%s: vendor lists %s, selection is %s", path, e.Version, ver))
			continue
		}
		pm := proxy[effPath]
		if pm == nil {
			diag = append(diag, fmt.Sprintf("%s: vendor references unknown module path", effPath))
			continue
		}
		found := false
		for _, v := range pm.Versions {
			if v == effVer {
				found = true
				break
			}
		}
		if !found {
			diag = append(diag, fmt.Sprintf("%s: vendor references %s@%s which the proxy does not publish", path, effPath, effVer))
		}
	}
	sort.Strings(diag)
	return len(diag) == 0, diag
}

func trimIncompatibleSuffix(v string) string {
	if i := strings.Index(v, "+"); i >= 0 {
		return v[:i]
	}
	return v
}
