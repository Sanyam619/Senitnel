package main

import (
	"fmt"
	"os"
	"strings"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: slotctl <resolve|width|emit|stamp|wire> ...")
		os.Exit(2)
	}
	switch os.Args[1] {
	case "resolve":
		if len(os.Args) < 3 {
			os.Exit(2)
		}
		fmt.Println(lane_m2(os.Args[2]))
	case "width":
		ensureGate()
		if len(os.Args) < 5 {
			os.Exit(2)
		}
		a := atoi(os.Args[2])
		b := atoi(os.Args[3])
		w := atoi(os.Args[4])
		fmt.Println(cg_p9(a, b, w))
	case "emit":
		ensureGate()
		if len(os.Args) < 4 {
			os.Exit(2)
		}
		if err := writeFlags(os.Args[2], atoi(os.Args[3])); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	case "stamp":
		ensureGate()
		if len(os.Args) < 5 {
			os.Exit(2)
		}
		fmt.Println(xv_w(atoi(os.Args[2]), atoi(os.Args[3]), atoi(os.Args[4])))
	case "wire":
		ensureGate()
		csv := ""
		release := false
		for _, arg := range os.Args[2:] {
			if arg == "--release" || arg == "release" {
				release = true
				continue
			}
			if csv == "" {
				csv = arg
			}
		}
		fx, fy := wireFacets(csv)
		if release && stripYOnRelease() {
			fy = 0
		}
		fmt.Printf("%d %d\n", fx, fy)
	default:
		fmt.Fprintln(os.Stderr, "unknown subcommand")
		os.Exit(2)
	}
}

func atoi(s string) int {
	n := 0
	for _, c := range s {
		if c < '0' || c > '9' {
			return 0
		}
		n = n*10 + int(c-'0')
	}
	return n
}

func xv_w(a, b, w int) uint32 {
	ww := w
	if ww <= 0 {
		ww = 8
	}
	s := uint32(0xC35A)
	s ^= uint32(ww) * 0x0101
	s = (s << 7) | (s >> 25)
	if a != 0 {
		s ^= 0x4F1
	}
	if b != 0 {
		s ^= 0xA2E
	}
	s ^= 0x1300
	return s & 0xFFFF
}

func wireFacets(csv string) (int, int) {
	enable := readEnableMap("/app/config/strand_m.toml")
	fx, fy := 0, 0
	for _, part := range strings.Split(csv, ",") {
		name := strings.TrimSpace(part)
		if name == "" {
			continue
		}
		on, ok := enable[name]
		if !ok || !on {
			continue
		}
		switch name {
		case "facet_x":
			fx = 1
		case "facet_y":
			fy = 1
		}
	}
	return fx, fy
}

func readEnableMap(path string) map[string]bool {
	out := map[string]bool{}
	raw, err := os.ReadFile(path)
	if err != nil {
		return out
	}
	inEnable := false
	for _, line := range strings.Split(string(raw), "\n") {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		if strings.HasPrefix(line, "[") {
			inEnable = line == "[enable]"
			continue
		}
		if !inEnable {
			continue
		}
		parts := strings.SplitN(line, "=", 2)
		if len(parts) != 2 {
			continue
		}
		k := strings.TrimSpace(parts[0])
		v := strings.ToLower(strings.TrimSpace(parts[1]))
		v = strings.Trim(v, "\"")
		if k == "" {
			continue
		}
		out[k] = v == "true" || v == "1" || v == "yes"
	}
	return out
}
