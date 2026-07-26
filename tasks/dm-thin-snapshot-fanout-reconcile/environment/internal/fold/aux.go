package fold

import (
	"bufio"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"
)

type Row struct {
	Gen    uint64
	Seq    uint64
	Drill  string
	Tip    string
	Origin string
	Kind   string
	Epoch  uint32
	Floor  uint32
}

func ingest_x(path string) ([]Row, error) {
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
		parts := strings.Split(line, "|")
		if len(parts) < 8 {
			return nil, fmt.Errorf("bad wal line: %s", line)
		}
		gen, err := strconv.ParseUint(parts[0], 10, 64)
		if err != nil {
			return nil, err
		}
		seq, err := strconv.ParseUint(parts[1], 10, 64)
		if err != nil {
			return nil, err
		}
		ep, err := strconv.ParseUint(parts[6], 10, 32)
		if err != nil {
			return nil, err
		}
		fl, err := strconv.ParseUint(parts[7], 10, 32)
		if err != nil {
			return nil, err
		}
		out = append(out, Row{
			Gen: gen, Seq: seq, Drill: parts[2], Tip: parts[3],
			Origin: parts[4], Kind: parts[5], Epoch: uint32(ep), Floor: uint32(fl),
		})
	}
	return out, sc.Err()
}

func RowsY(root string) ([]Row, error) {
	path := filepath.Join(root, "meta", "runtime.tsv")
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	var out []Row
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "" {
			continue
		}
		parts := strings.Split(line, "\t")
		if len(parts) < 7 {
			return nil, fmt.Errorf("bad runtime line: %s", line)
		}
		ep, _ := strconv.ParseUint(parts[5], 10, 32)
		fl, _ := strconv.ParseUint(parts[6], 10, 32)
		out = append(out, Row{
			Drill: parts[1], Tip: parts[2], Origin: parts[3], Kind: parts[4],
			Epoch: uint32(ep), Floor: uint32(fl),
		})
	}
	return out, sc.Err()
}

func CapZ(path string) (uint64, error) {
	b, err := os.ReadFile(path)
	if err != nil {
		return 0, err
	}
	for _, line := range strings.Split(string(b), "\n") {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		return strconv.ParseUint(line, 10, 64)
	}
	return 0, fmt.Errorf("empty seal")
}

func ScrubW(root string) error {
	rows, err := RowsY(root)
	if err != nil {
		return err
	}
	var b strings.Builder
	b.WriteString("# activation tips\n[tips]\n")
	for _, r := range rows {
		b.WriteString(fmt.Sprintf("%s = %q\n", r.Drill, r.Tip))
	}
	meta := filepath.Join(root, "meta", "activation.toml")
	return os.WriteFile(meta, []byte(b.String()), 0o644)
}
