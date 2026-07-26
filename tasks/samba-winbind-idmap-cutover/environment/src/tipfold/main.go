package main

import (
	"encoding/binary"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

type tip struct {
	kn            string
	lo, hi, rk, gen int
	tag           string
	ord           int
}

func fatal(f string, a ...any) {
	fmt.Fprintf(os.Stderr, "tipfold: "+f+"\n", a...)
	os.Exit(1)
}

func readSeal(path string) (string, int) {
	b, err := os.ReadFile(path)
	if err != nil {
		fatal("seal: %v", err)
	}
	s := strings.TrimSpace(string(b))
	var n int
	fmt.Sscanf(s, "%d", &n)
	return s, n
}

func loadTips(path string) []tip {
	b, err := os.ReadFile(path)
	if err != nil {
		fatal("tips: %v", err)
	}
	if len(b) < 8 || string(b[:4]) != "TIP2" {
		fatal("bad tips magic")
	}
	n := int(binary.BigEndian.Uint32(b[4:8]))
	off := 8
	out := make([]tip, 0, n)
	for i := 0; i < n; i++ {
		if off+4 > len(b) {
			fatal("truncated tip")
		}
		gen := int(binary.BigEndian.Uint16(b[off : off+2]))
		rk := int(b[off+2])
		flags := int(b[off+3])
		off += 4
		if off >= len(b) {
			fatal("truncated kn len")
		}
		knLen := int(b[off])
		off++
		if off+knLen+8 > len(b) {
			fatal("truncated kn/span")
		}
		kn := string(b[off : off+knLen])
		off += knLen
		lo := int(binary.BigEndian.Uint32(b[off : off+4]))
		hi := int(binary.BigEndian.Uint32(b[off+4 : off+8]))
		off += 8
		tag := ""
		if flags&1 != 0 {
			if off >= len(b) {
				fatal("truncated tag len")
			}
			tl := int(b[off])
			off++
			if off+tl > len(b) {
				fatal("truncated tag")
			}
			tag = string(b[off : off+tl])
			off += tl
		}
		out = append(out, tip{kn: kn, lo: lo, hi: hi, rk: rk, gen: gen, tag: tag, ord: i})
	}
	return out
}

func main() {
	root := getenv("SAMBA_VAR", "/var/lib/samba")
	etc := getenv("SAMBA_ETC", "/etc/samba")
	sealPath := getenv("DESK_SEAL", filepath.Join(etc, "desk.seal"))
	tipsPath := filepath.Join(root, "journal", "tips.bin")
	meta := filepath.Join(root, "meta")
	modePath := filepath.Join(meta, "pref.mode")
	armedPath := filepath.Join(meta, "pref.armed")

	sealStr, sealN := readSeal(sealPath)
	modeB, err := os.ReadFile(modePath)
	if err != nil {
		fatal("pref.mode: %v", err)
	}
	mode := strings.TrimSpace(string(modeB))
	if mode != "equality-inclusive" {
		fatal("pref mode %q", mode)
	}
	armedB, err := os.ReadFile(armedPath)
	if err != nil {
		fatal("pref.armed missing")
	}
	if strings.TrimSpace(string(armedB)) != sealStr {
		fatal("pref.armed must equal desk.seal")
	}

	tips := loadTips(tipsPath)
	var best *tip
	for i := range tips {
		t := &tips[i]
		if t.gen > sealN {
			continue
		}
		if t.tag != "" {
			continue
		}
		if best == nil || t.rk > best.rk || (t.rk == best.rk && t.ord > best.ord) {
			best = t
		}
	}
	if best == nil {
		fatal("no eligible tip")
	}
	if err := os.MkdirAll(meta, 0o755); err != nil {
		fatal("mkdir: %v", err)
	}
	body := fmt.Sprintf("kn=%s\nlo=%d\nhi=%d\nrk=%d\n", best.kn, best.lo, best.hi, best.rk)
	if err := os.WriteFile(filepath.Join(meta, "backends.toml"), []byte(body), 0o644); err != nil {
		fatal("write backends: %v", err)
	}
	if err := os.WriteFile(filepath.Join(meta, "tip.ok"), []byte(sealStr+"\n"), 0o644); err != nil {
		fatal("tip.ok: %v", err)
	}
}

func getenv(k, d string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return d
}
