package labcfg

import (
	"os"
	"strconv"
	"strings"
)

func TailPadBytes() int {
	raw, err := os.ReadFile("/opt/lab/config/lab.toml")
	if err != nil {
		return 0
	}
	for _, line := range strings.Split(string(raw), "\n") {
		line = strings.TrimSpace(line)
		if strings.HasPrefix(line, "tail_pad_bytes") {
			parts := strings.SplitN(line, "=", 2)
			if len(parts) != 2 {
				continue
			}
			v, err := strconv.Atoi(strings.TrimSpace(parts[1]))
			if err == nil {
				return v
			}
		}
	}
	return 0
}
