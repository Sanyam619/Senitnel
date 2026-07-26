package internal

import (
	"os"
	"strings"
)

// PreferDurable reports whether host preference binds durable authority.
func PreferDurable() bool {
	raw, err := os.ReadFile("/app/ops/prefer.toml")
	if err != nil {
		return false
	}
	root := ""
	bind := ""
	for _, line := range strings.Split(string(raw), "\n") {
		line = strings.TrimSpace(line)
		if strings.HasPrefix(line, "root") {
			parts := strings.SplitN(line, "=", 2)
			if len(parts) == 2 {
				root = strings.Trim(strings.TrimSpace(parts[1]), "\"")
			}
		}
		if strings.HasPrefix(line, "bind") {
			parts := strings.SplitN(line, "=", 2)
			if len(parts) == 2 {
				bind = strings.Trim(strings.TrimSpace(parts[1]), "\"")
			}
		}
	}
	return root == "durable" && bind == "authority"
}
