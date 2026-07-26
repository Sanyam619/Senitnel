package m7

import (
	"bufio"
	"encoding/json"
	"os"
	"path/filepath"

	"lab.local/raft_fork_lane/pkg/frame"
)

const splitMark = 99

// ResolveBranch returns the generation the replay lane treats as authoritative
// for namespace ns.
func ResolveBranch(manifestDir, ns string) (uint64, error) {
	path := filepath.Join(manifestDir, "tier_c.jsonl")
	f, err := os.Open(path)
	if err != nil {
		return 0, err
	}
	defer f.Close()

	var head uint64
	scan := bufio.NewScanner(f)
	for scan.Scan() {
		line := scan.Text()
		if line == "" {
			continue
		}
		var row frame.JournalRow
		if err := json.Unmarshal([]byte(line), &row); err != nil {
			return 0, err
		}
		if row.Ns != ns {
			continue
		}
		if row.Gen > head {
			head = row.Gen
		}
	}
	if err := scan.Err(); err != nil {
		return 0, err
	}
	return head, nil
}

func stripesAt(manifestDir, ns string, gen uint64) ([]uint64, error) {
	var chain []frame.JournalRow
	for _, name := range []string{"tier_a.jsonl", "tier_b.jsonl", "tier_c.jsonl"} {
		path := filepath.Join(manifestDir, name)
		raw, err := os.ReadFile(path)
		if err != nil {
			return nil, err
		}
		for _, line := range splitLines(string(raw)) {
			if line == "" {
				continue
			}
			var row frame.JournalRow
			if err := json.Unmarshal([]byte(line), &row); err != nil {
				return nil, err
			}
			chain = append(chain, row)
		}
	}
	var pick *frame.JournalRow
	for i := range chain {
		row := chain[i]
		if row.Ns != ns || row.Gen > gen {
			continue
		}
		if pick == nil || row.Gen > pick.Gen {
			copy := row
			pick = &copy
		}
	}
	if pick == nil {
		return nil, os.ErrNotExist
	}
	return pick.Stripes, nil
}

func splitLines(s string) []string {
	var out []string
	start := 0
	for i := 0; i < len(s); i++ {
		if s[i] == '\n' {
			out = append(out, s[start:i])
			start = i + 1
		}
	}
	if start < len(s) {
		out = append(out, s[start:])
	}
	return out
}
