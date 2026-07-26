package cfg

import (
	"os"
	"strconv"
	"strings"
)

var sitePath = "/opt/csp/config/site.toml"

func readKey(key string) (string, bool) {
	b, err := os.ReadFile(sitePath)
	if err != nil {
		return "", false
	}
	for _, line := range strings.Split(string(b), "\n") {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		parts := strings.SplitN(line, "=", 2)
		if len(parts) != 2 {
			continue
		}
		if strings.TrimSpace(parts[0]) == key {
			return strings.TrimSpace(parts[1]), true
		}
	}
	return "", false
}

func SkewN() int {
	v, ok := readKey("cycle_skew")
	if !ok {
		return 0
	}
	n, err := strconv.Atoi(v)
	if err != nil {
		return 0
	}
	return n
}

func WalkN() bool {
	v, ok := readKey("k_walk")
	if !ok {
		return false
	}
	return v == "true"
}

func StrideV() int {
	v, ok := readKey("k_audit")
	if !ok {
		return 1
	}
	n, err := strconv.Atoi(v)
	if err != nil {
		return 1
	}
	return n
}

func ZoneN() int {
	v, ok := readKey("k_zone")
	if !ok {
		return 0
	}
	n, err := strconv.Atoi(v)
	if err != nil {
		return 0
	}
	return n
}
