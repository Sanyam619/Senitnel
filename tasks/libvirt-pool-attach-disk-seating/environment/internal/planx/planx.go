package planx

import (
	"bufio"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

// Row is one seating request drawn from the roster.
type Row struct {
	Domain string
	Target string
	Pool   string
	Volume string
}

// Ident is a resolved pool identity: its bound UUID and target path.
type Ident struct {
	UUID string
	Path string
}

// RosterRows reads the seating roster (domain|target|pool|volume per line).
func RosterRows(path string) ([]Row, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	var out []Row
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		p := strings.Split(line, "|")
		if len(p) < 4 {
			continue
		}
		out = append(out, Row{Domain: p[0], Target: p[1], Pool: p[2], Volume: p[3]})
	}
	return out, sc.Err()
}

// PlanMap reads the staged plan (pool<TAB>uuid<TAB>path) into a lookup.
func PlanMap(path string) (map[string]Ident, error) {
	out := map[string]Ident{}
	f, err := os.Open(path)
	if err != nil {
		if os.IsNotExist(err) {
			return out, nil
		}
		return nil, err
	}
	defer f.Close()
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		p := strings.Split(line, "\t")
		if len(p) < 3 {
			continue
		}
		out[p[0]] = Ident{UUID: strings.TrimSpace(p[1]), Path: strings.TrimSpace(p[2])}
	}
	return out, sc.Err()
}

// SelectMode reads the highest-priority selection drop-in and returns the
// requested preference. The default when nothing selects it is "surface".
func SelectMode(dir string) string {
	ents, err := os.ReadDir(dir)
	if err != nil {
		return "surface"
	}
	names := make([]string, 0, len(ents))
	for _, e := range ents {
		if e.IsDir() {
			continue
		}
		if strings.HasSuffix(e.Name(), ".conf") {
			names = append(names, e.Name())
		}
	}
	sort.Strings(names)
	mode := "surface"
	for _, n := range names {
		b, err := os.ReadFile(filepath.Join(dir, n))
		if err != nil {
			continue
		}
		for _, line := range strings.Split(string(b), "\n") {
			line = strings.TrimSpace(line)
			if strings.HasPrefix(line, "authority=") {
				mode = strings.TrimSpace(strings.TrimPrefix(line, "authority="))
			}
		}
	}
	return mode
}
