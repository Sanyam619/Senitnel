package internal

import "strings"

func skim_fold(req string) int {
	if strings.HasPrefix(req, "/data/") {
		return 1
	}
	return 0
}
