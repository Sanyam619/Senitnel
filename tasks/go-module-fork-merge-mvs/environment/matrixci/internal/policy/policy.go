package policy

import (
	"fmt"
	"os"
	"sort"
	"strings"
)

// RequiredExclude names a module path/version pair that must be present as
// an `exclude` directive in the root go.mod.
type RequiredExclude struct {
	Path    string
	Version string
}

// RetainedFork names a replace directive retained across every workspace
// go.mod, targeting ForkPath at a version >= MinVersion.
type RetainedFork struct {
	Path       string
	ForkPath   string
	MinVersion string
}

// Constraints is the full parsed policy document.
type Constraints struct {
	Floors             map[string]string
	Caps               map[string]string
	RequiredExcludes   []RequiredExclude
	RetainedForks      []RetainedFork
	ProhibitedReplaces map[string]bool
}

// Load parses the markdown security-pin-policy file and returns the full
// constraints set. Each supported table is detected by its header row
// pattern and parsed independently; unrecognized tables are ignored.
func Load(path string) (*Constraints, error) {
	b, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	lines := strings.Split(string(b), "\n")

	c := &Constraints{
		Floors:             map[string]string{},
		Caps:               map[string]string{},
		ProhibitedReplaces: map[string]bool{},
	}

	tables := extractTables(lines)
	for _, t := range tables {
		switch classifyTable(t.header) {
		case "window":
			parseWindow(t, c)
		case "required_exclude":
			parseRequiredExcludes(t, c)
		case "retained_fork":
			parseRetainedForks(t, c)
		case "prohibited_replace":
			parseProhibited(t, c)
		}
	}
	return c, nil
}

// LoadFloors is retained for backward compatibility with callers that only
// need the floor map.
func LoadFloors(path string) (map[string]string, error) {
	c, err := Load(path)
	if err != nil {
		return nil, err
	}
	return c.Floors, nil
}

// table represents a parsed markdown table with a header row and body rows.
type table struct {
	header []string
	rows   [][]string
}

func extractTables(lines []string) []table {
	var out []table
	i := 0
	for i < len(lines) {
		trim := strings.TrimSpace(lines[i])
		if strings.HasPrefix(trim, "|") && strings.HasSuffix(trim, "|") {
			// Candidate header. Peek next line for the separator row.
			if i+1 < len(lines) && strings.Contains(lines[i+1], "---") {
				hdr := splitTableRow(trim)
				var rows [][]string
				j := i + 2
				for j < len(lines) {
					r := strings.TrimSpace(lines[j])
					if !strings.HasPrefix(r, "|") || !strings.HasSuffix(r, "|") {
						break
					}
					rows = append(rows, splitTableRow(r))
					j++
				}
				out = append(out, table{header: hdr, rows: rows})
				i = j
				continue
			}
		}
		i++
	}
	return out
}

func classifyTable(header []string) string {
	lower := make([]string, len(header))
	for i, h := range header {
		lower[i] = strings.ToLower(strings.TrimSpace(h))
	}
	// Version window table: has both "floor" and "max"
	hasFloor := false
	hasMax := false
	hasExcludedVer := false
	hasForkPath := false
	hasMinFork := false
	hasModule := false
	for _, h := range lower {
		if strings.Contains(h, "floor") {
			hasFloor = true
		}
		if strings.Contains(h, "max") {
			hasMax = true
		}
		if strings.Contains(h, "excluded version") {
			hasExcludedVer = true
		}
		if strings.Contains(h, "fork path") {
			hasForkPath = true
		}
		if strings.Contains(h, "min fork") {
			hasMinFork = true
		}
		if strings.HasPrefix(h, "module") {
			hasModule = true
		}
	}
	if hasModule && hasFloor && hasMax {
		return "window"
	}
	if hasModule && hasExcludedVer {
		return "required_exclude"
	}
	if hasModule && hasForkPath && hasMinFork {
		return "retained_fork"
	}
	if hasModule && len(header) == 1 {
		return "prohibited_replace"
	}
	return ""
}

func parseWindow(t table, c *Constraints) {
	// Columns: Module | Floor version | Max version | ...
	for _, r := range t.rows {
		if len(r) < 3 {
			continue
		}
		mod := strings.TrimSpace(r[0])
		floor := strings.TrimSpace(r[1])
		cap := strings.TrimSpace(r[2])
		if mod == "" || floor == "" || cap == "" {
			continue
		}
		c.Floors[mod] = floor
		c.Caps[mod] = cap
	}
}

func parseRequiredExcludes(t table, c *Constraints) {
	for _, r := range t.rows {
		if len(r) < 2 {
			continue
		}
		mod := strings.TrimSpace(r[0])
		ver := strings.TrimSpace(r[1])
		if mod == "" || ver == "" {
			continue
		}
		c.RequiredExcludes = append(c.RequiredExcludes, RequiredExclude{Path: mod, Version: ver})
	}
}

func parseRetainedForks(t table, c *Constraints) {
	// Columns: Module | Fork path | Min fork version
	for _, r := range t.rows {
		if len(r) < 3 {
			continue
		}
		mod := strings.TrimSpace(r[0])
		fork := strings.TrimSpace(r[1])
		minVer := strings.TrimSpace(r[2])
		if mod == "" || fork == "" || minVer == "" {
			continue
		}
		c.RetainedForks = append(c.RetainedForks, RetainedFork{
			Path:       mod,
			ForkPath:   fork,
			MinVersion: minVer,
		})
	}
}

func parseProhibited(t table, c *Constraints) {
	for _, r := range t.rows {
		if len(r) == 0 {
			continue
		}
		mod := strings.TrimSpace(r[0])
		if mod == "" {
			continue
		}
		c.ProhibitedReplaces[mod] = true
	}
}

func splitTableRow(row string) []string {
	row = strings.TrimPrefix(row, "|")
	row = strings.TrimSuffix(row, "|")
	parts := strings.Split(row, "|")
	out := make([]string, 0, len(parts))
	for _, p := range parts {
		out = append(out, strings.TrimSpace(p))
	}
	return out
}

// FloorViolations returns per-module strings describing selected versions
// below the pinned floor.
func FloorViolations(selected map[string]string, floors map[string]string) []string {
	var hits []string
	keys := sortedKeys(selected)
	for _, path := range keys {
		floor, ok := floors[path]
		if !ok {
			continue
		}
		if verCompare(selected[path], floor) < 0 {
			hits = append(hits, fmt.Sprintf("below-floor:%s", path))
		}
	}
	sort.Strings(hits)
	return hits
}

// CapViolations returns per-module strings describing selected versions
// above the policy-declared maximum.
func CapViolations(selected map[string]string, caps map[string]string) []string {
	var hits []string
	keys := sortedKeys(selected)
	for _, path := range keys {
		cap, ok := caps[path]
		if !ok {
			continue
		}
		if verCompare(selected[path], cap) > 0 {
			hits = append(hits, fmt.Sprintf("above-cap:%s", path))
		}
	}
	sort.Strings(hits)
	return hits
}

// SummarizeFloor produces a JSON-friendly summary indicating whether every
// window-guarded module resolves inside its `[floor, max]` window.
func SummarizeFloor(selected map[string]string, c *Constraints) map[string]interface{} {
	summary := map[string]interface{}{
		"respected":     true,
		"modules":       []map[string]string{},
	}
	respected := true
	var rows []map[string]string
	keys := sortedKeys(c.Floors)
	for _, path := range keys {
		row := map[string]string{
			"module":   path,
			"floor":    c.Floors[path],
			"max":      c.Caps[path],
			"selected": selected[path],
		}
		sel := selected[path]
		switch {
		case sel == "":
			row["status"] = "unresolved"
			respected = false
		case verCompare(sel, c.Floors[path]) < 0:
			row["status"] = "below-floor"
			respected = false
		case c.Caps[path] != "" && verCompare(sel, c.Caps[path]) > 0:
			row["status"] = "above-max"
			respected = false
		default:
			row["status"] = "ok"
		}
		rows = append(rows, row)
	}
	summary["respected"] = respected
	summary["modules"] = rows
	return summary
}

// SummarizeRequiredExcludes reports, for each policy-required exclude,
// whether it is currently declared in the root or sub go.mod exclude set.
func SummarizeRequiredExcludes(required []RequiredExclude, declared map[string]map[string]bool) map[string]interface{} {
	respected := true
	rows := []map[string]interface{}{}
	for _, e := range required {
		isDecl := declared[e.Path] != nil && declared[e.Path][e.Version]
		if !isDecl {
			respected = false
		}
		rows = append(rows, map[string]interface{}{
			"module":   e.Path,
			"version":  e.Version,
			"declared": isDecl,
		})
	}
	return map[string]interface{}{
		"respected": respected,
		"entries":   rows,
	}
}

// SummarizeProhibitedReplaces returns the sorted list of prohibited-replace
// violations discovered in either the root or sub go.mod replace tables.
func SummarizeProhibitedReplaces(hits []string) map[string]interface{} {
	return map[string]interface{}{
		"respected": len(hits) == 0,
		"entries":   hits,
	}
}

// SummarizeRetainedForks reports whether each policy-retained fork replace
// is currently declared with an acceptable fork path and version.
func SummarizeRetainedForks(required []RetainedFork, hits []string) map[string]interface{} {
	rows := make([]map[string]interface{}, 0, len(required))
	for _, f := range required {
		rows = append(rows, map[string]interface{}{
			"module":           f.Path,
			"fork_path":        f.ForkPath,
			"min_fork_version": f.MinVersion,
		})
	}
	return map[string]interface{}{
		"respected": len(hits) == 0,
		"entries":   rows,
		"violations": hits,
	}
}

func verCompare(a, b string) int {
	aa := trimIncompat(strings.TrimPrefix(a, "v"))
	bb := trimIncompat(strings.TrimPrefix(b, "v"))
	ap := strings.Split(aa, ".")
	bp := strings.Split(bb, ".")
	for i := 0; i < maxInt(len(ap), len(bp)); i++ {
		var an, bn int
		if i < len(ap) {
			an = atoiSafe(ap[i])
		}
		if i < len(bp) {
			bn = atoiSafe(bp[i])
		}
		if an != bn {
			if an < bn {
				return -1
			}
			return 1
		}
	}
	return 0
}

func trimIncompat(s string) string {
	if i := strings.Index(s, "+"); i >= 0 {
		return s[:i]
	}
	return s
}

func maxInt(a, b int) int {
	if a > b {
		return a
	}
	return b
}

func atoiSafe(s string) int {
	n := 0
	for _, c := range strings.TrimSpace(s) {
		if c < '0' || c > '9' {
			break
		}
		n = n*10 + int(c-'0')
	}
	return n
}

func sortedKeys(m map[string]string) []string {
	out := make([]string, 0, len(m))
	for k := range m {
		out = append(out, k)
	}
	sort.Strings(out)
	return out
}
