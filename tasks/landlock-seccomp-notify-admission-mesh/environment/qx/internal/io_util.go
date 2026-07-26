package internal

import (
	"bufio"
	"encoding/json"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
)

type scen struct {
	ID         string `json:"id"`
	JobID      string `json:"job_id"`
	Req        string `json:"req"`
	Op         string `json:"op"`
	Wire       string `json:"wire"`
	FdEpoch    int64  `json:"fd_epoch"`
	Claim      int64  `json:"claim"`
	Epoch      int64  `json:"epoch"`
	Lane       int    `json:"lane"`
	Ts         int64  `json:"ts"`
	PayloadHex string `json:"payload_hex"`
	Check      int    `json:"check"`
}

func LoadScenarios(dir string) ([]scen, error) {
	entries, err := os.ReadDir(dir)
	if err != nil {
		return nil, err
	}
	var out []scen
	for _, e := range entries {
		if e.IsDir() || !stringsHasSuffix(e.Name(), ".json") {
			continue
		}
		raw, err := os.ReadFile(filepath.Join(dir, e.Name()))
		if err != nil {
			return nil, err
		}
		var s scen
		if err := json.Unmarshal(raw, &s); err != nil {
			return nil, err
		}
		out = append(out, s)
	}
	sort.Slice(out, func(i, j int) bool { return out[i].ID < out[j].ID })
	return out, nil
}

func stringsHasSuffix(s, suf string) bool {
	return len(s) >= len(suf) && s[len(s)-len(suf):] == suf
}

func loadMap(src string) (map[string]string, error) {
	f, err := os.Open(src)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	out := make(map[string]string)
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		parts := strings.SplitN(line, "=", 2)
		if len(parts) != 2 {
			continue
		}
		out[strings.TrimSpace(parts[0])] = strings.TrimSpace(parts[1])
	}
	return out, sc.Err()
}

func loadJournal(src string) (map[string]string, error) {
	raw, err := os.ReadFile(src)
	if err != nil {
		return nil, err
	}
	out := make(map[string]string)
	for _, line := range strings.Split(string(raw), "\n") {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		var row map[string]string
		if err := json.Unmarshal([]byte(line), &row); err != nil {
			continue
		}
		alias := row["alias"]
		if alias == "" {
			continue
		}
		if c := row["canon"]; c != "" {
			out[alias] = c
		} else if v := row["via"]; v != "" {
			out[alias] = v
		}
	}
	return out, nil
}

func loadList(src string) ([]string, error) {
	raw, err := os.ReadFile(src)
	if err != nil {
		return nil, err
	}
	var out []string
	for _, line := range strings.Split(string(raw), "\n") {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		out = append(out, line)
	}
	return out, nil
}

func readEpoch(src string) (int64, error) {
	raw, err := os.ReadFile(src)
	if err != nil {
		return 0, err
	}
	s := strings.TrimSpace(string(raw))
	idx := strings.Index(s, "\"epoch\"")
	if idx < 0 {
		return 0, os.ErrInvalid
	}
	rest := s[idx:]
	colon := strings.Index(rest, ":")
	if colon < 0 {
		return 0, os.ErrInvalid
	}
	num := strings.TrimSpace(rest[colon+1:])
	num = strings.TrimRight(num, "}\n\r\t ,")
	return strconv.ParseInt(num, 10, 64)
}

func readWindow(src string) (int64, int64, []string, error) {
	raw, err := os.ReadFile(src)
	if err != nil {
		return 0, 0, nil, err
	}
	var lo, hi int64
	var marks []string
	for _, line := range strings.Split(string(raw), "\n") {
		line = strings.TrimSpace(line)
		if strings.HasPrefix(line, "lo") {
			parts := strings.SplitN(line, "=", 2)
			if len(parts) == 2 {
				lo, _ = strconv.ParseInt(strings.TrimSpace(parts[1]), 10, 64)
			}
		} else if strings.HasPrefix(line, "hi") {
			parts := strings.SplitN(line, "=", 2)
			if len(parts) == 2 {
				hi, _ = strconv.ParseInt(strings.TrimSpace(parts[1]), 10, 64)
			}
		} else if strings.HasPrefix(line, "marks") {
			parts := strings.SplitN(line, "=", 2)
			if len(parts) == 2 {
				inner := strings.TrimSpace(parts[1])
				inner = strings.TrimPrefix(inner, "[")
				inner = strings.TrimSuffix(inner, "]")
				for _, tok := range strings.Split(inner, ",") {
					tok = strings.TrimSpace(tok)
					tok = strings.Trim(tok, "\"'")
					if tok != "" {
						marks = append(marks, tok)
					}
				}
			}
		}
	}
	return lo, hi, marks, nil
}

func loadStrand(path string) int {
	raw, err := os.ReadFile(path)
	if err != nil {
		return 0
	}
	for _, line := range strings.Split(string(raw), "\n") {
		line = strings.TrimSpace(line)
		if strings.HasPrefix(line, "strand") {
			parts := strings.SplitN(line, "=", 2)
			if len(parts) == 2 {
				v := strings.TrimSpace(parts[1])
				v = strings.Trim(v, "\"")
				n, _ := strconv.Atoi(v)
				return n
			}
		}
	}
	return 0
}

func loadSeedHex(path string) (string, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return "", err
	}
	var obj map[string]any
	if err := json.Unmarshal(raw, &obj); err != nil {
		return "", err
	}
	if s, ok := obj["seed_hex"].(string); ok {
		return s, nil
	}
	return "", os.ErrInvalid
}
