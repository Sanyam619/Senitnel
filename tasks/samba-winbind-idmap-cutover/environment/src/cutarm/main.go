package main

import (
	"encoding/binary"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

func fatal(f string, a ...any) {
	fmt.Fprintf(os.Stderr, "cutarm: "+f+"\n", a...)
	os.Exit(1)
}

type row struct {
	kind, mode, gen int
	hold            string
}

func loadJournal(path string) []row {
	b, err := os.ReadFile(path)
	if err != nil {
		fatal("journal: %v", err)
	}
	if len(b) < 8 || string(b[:4]) != "JRN2" {
		fatal("bad journal magic")
	}
	n := int(binary.BigEndian.Uint32(b[4:8]))
	off := 8
	out := make([]row, 0, n)
	for i := 0; i < n; i++ {
		if off+4 > len(b) {
			fatal("truncated row")
		}
		kind := int(b[off])
		mode := int(b[off+1])
		gen := int(binary.BigEndian.Uint16(b[off+2 : off+4]))
		off += 4
		if off >= len(b) {
			fatal("truncated hold len")
		}
		hl := int(b[off])
		off++
		if off+hl > len(b) {
			fatal("truncated hold")
		}
		hold := string(b[off : off+hl])
		off += hl
		out = append(out, row{kind: kind, mode: mode, gen: gen, hold: hold})
	}
	return out
}

func main() {
	root := getenv("SAMBA_VAR", "/var/lib/samba")
	etc := getenv("SAMBA_ETC", "/etc/samba")
	envPath := getenv("SAMBA_DESKD_ENV", filepath.Join(etc, "deskd.env"))
	meta := filepath.Join(root, "meta")
	jpath := filepath.Join(root, "ops", "journal.bin")

	targetB, err := os.ReadFile(filepath.Join(meta, "gen.target"))
	if err != nil {
		fatal("gen.target: %v", err)
	}
	var target int
	fmt.Sscanf(strings.TrimSpace(string(targetB)), "%d", &target)

	tipOK, err := os.ReadFile(filepath.Join(meta, "tip.ok"))
	if err != nil {
		fatal("tip.ok required before cutover arm")
	}
	sealB, err := os.ReadFile(getenv("DESK_SEAL", filepath.Join(etc, "desk.seal")))
	if err != nil {
		fatal("seal: %v", err)
	}
	seal := strings.TrimSpace(string(sealB))
	if strings.TrimSpace(string(tipOK)) != seal {
		fatal("tip.ok mismatch")
	}

	rows := loadJournal(jpath)
	var chosen *row
	for i := range rows {
		r := &rows[i]
		// kind 2 = cutover, mode 2 = seal
		if r.kind == 2 && r.mode == 2 && r.gen == target {
			chosen = r
		}
	}
	if chosen == nil {
		fatal("missing sealed cutover for target gen")
	}

	if err := os.MkdirAll(meta, 0o755); err != nil {
		fatal("mkdir: %v", err)
	}
	_ = os.WriteFile(filepath.Join(meta, "gen.live"), []byte(fmt.Sprintf("%d\n", target)), 0o644)
	_ = os.WriteFile(filepath.Join(meta, "attach.intent"), []byte("seal\n"), 0o644)
	_ = os.WriteFile(filepath.Join(meta, "hold.token"), []byte(chosen.hold+"\n"), 0o644)
	_ = os.WriteFile(filepath.Join(meta, "cutover.ok"), []byte(fmt.Sprintf("gen=%d\nhold=%s\nmode=seal\n", target, chosen.hold)), 0o644)

	text := ""
	if b, err := os.ReadFile(envPath); err == nil {
		text = string(b)
	}
	var lines []string
	for _, ln := range strings.Split(text, "\n") {
		if strings.HasPrefix(ln, "HOLD_TOKEN=") || strings.HasPrefix(ln, "PAYLOAD_LINEAGE=") {
			continue
		}
		if strings.TrimSpace(ln) != "" {
			lines = append(lines, ln)
		}
	}
	lines = append(lines, "PAYLOAD_LINEAGE=sealed")
	lines = append(lines, "HOLD_TOKEN="+chosen.hold)
	if err := os.WriteFile(envPath, []byte(strings.Join(lines, "\n")+"\n"), 0o644); err != nil {
		fatal("deskd.env: %v", err)
	}
}

func getenv(k, d string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return d
}
