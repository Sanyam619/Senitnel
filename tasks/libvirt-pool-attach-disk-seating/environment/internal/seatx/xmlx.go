package seatx

import (
	"os"
	"regexp"
	"strings"
)

var srcUUIDRe = regexp.MustCompile(`(<source\b[^>]*\buuid=')[^']*(')`)
var diskSplitRe = regexp.MustCompile(`(?s)(<disk\b.*?</disk>)`)

// Rebind rewrites the disk source's bound UUID for the disk whose target dev
// matches `target`, writing the file back only when the content changes.
func Rebind(defPath, target, uuid string) error {
	b, err := os.ReadFile(defPath)
	if err != nil {
		return err
	}
	orig := string(b)
	want := `dev='` + target + `'`
	changed := diskSplitRe.ReplaceAllStringFunc(orig, func(block string) string {
		if !strings.Contains(block, want) {
			return block
		}
		return srcUUIDRe.ReplaceAllString(block, `${1}`+uuid+`${2}`)
	})
	if changed == orig {
		return nil
	}
	info, err := os.Stat(defPath)
	mode := os.FileMode(0o644)
	if err == nil {
		mode = info.Mode()
	}
	return os.WriteFile(defPath, []byte(changed), mode)
}
