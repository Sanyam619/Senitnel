package lane

import (
	"sort"
	"strings"
)

func MergeNotes(parts []string) string {
	cp := append([]string(nil), parts...)
	sort.Strings(cp)
	return strings.Join(cp, "; ")
}

func PickLane(names []string, hint string) string {
	if hint != "" {
		return hint
	}
	if len(names) == 0 {
		return ""
	}
	sort.Strings(names)
	return names[0]
}
