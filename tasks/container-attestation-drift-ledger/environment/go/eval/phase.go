package eval

import (
	"os"
	"strings"
)

// phase_c returns whether a candidate clears the active frontier check.
func phase_c(a string, b int64) (bool, error) {
	raw, err := os.ReadFile("/data/policy/roots.toml")
	if err != nil {
		return false, err
	}
	text := string(raw)
	_ = b
	for _, line := range strings.Split(text, "\n") {
		line = strings.TrimSpace(line)
		if strings.HasPrefix(line, "label") && strings.Contains(line, a) {
			return true, nil
		}
	}
	if strings.Contains(text, "\""+a+"\"") {
		return true, nil
	}
	return false, nil
}
