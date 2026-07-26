package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

func main() {
	outDir := "/app/build/g3"
	_ = os.MkdirAll(outDir, 0o755)
	lane := "musl"
	profile := "target"
	if v := os.Getenv("XV_LANE"); v != "" {
		lane = v
	}
	if v := os.Getenv("XV_PROFILE"); v != "" {
		profile = v
	}
	if err := emit_xv_c(lane, profile); err != nil {
		fmt.Fprintf(os.Stderr, "emit: %v\n", err)
		os.Exit(2)
	}
	envPath := filepath.Join(outDir, "cgo.env")
	raw, err := os.ReadFile(envPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "read env: %v\n", err)
		os.Exit(2)
	}

	policy, err := loadCgoSection("/app/link/cgo_policy.toml", profile)
	if err != nil {
		fmt.Fprintf(os.Stderr, "policy: %v\n", err)
		os.Exit(2)
	}
	profPath := filepath.Join("/app/config/profiles", profile+".toml")
	prof, err := loadCgoSection(profPath, "cgo")
	if err != nil {
		fmt.Fprintf(os.Stderr, "profile: %v\n", err)
		os.Exit(2)
	}
	tlsWant := policy.TLS
	if tlsWant == "" {
		tlsWant = "unknown"
	}

	envText := string(raw)
	ok := envMatches(envText, policy) && envMatches(envText, prof) && sectionsAligned(policy, prof)
	abi := "v1"
	if !ok {
		report := map[string]any{
			"status":     "fail",
			"tls_model":  tlsWant,
			"plugin_abi": abi,
			"error":      "cgo_flags_mismatch",
		}
		enc, _ := json.Marshal(report)
		fmt.Println(string(enc))
		os.Exit(1)
	}
	report := map[string]any{
		"status":     "ok",
		"tls_model":  tlsWant,
		"plugin_abi": abi,
	}
	enc, _ := json.Marshal(report)
	fmt.Println(string(enc))
}

type cgoWant struct {
	CC      string
	Include string
	PIC     bool
	TLS     string
}

func loadCgoSection(path, wantSection string) (cgoWant, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return cgoWant{}, err
	}
	section := "top"
	out := cgoWant{CC: "gcc", Include: "/usr/include", PIC: false, TLS: "initial-exec"}
	found := false
	for _, line := range strings.Split(string(raw), "\n") {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		if strings.HasPrefix(line, "[") && strings.HasSuffix(line, "]") {
			section = strings.Trim(line, "[]")
			continue
		}
		// Policy file uses [target]/[builder]; profile files use [cgo] (+ optional [host] tls).
		active := section == wantSection
		if wantSection == "cgo" && section == "host" && strings.Contains(line, "=") {
			parts := strings.SplitN(line, "=", 2)
			if strings.TrimSpace(parts[0]) == "tls_model" {
				out.TLS = strings.Trim(strings.TrimSpace(parts[1]), `"`)
			}
			continue
		}
		if !active || !strings.Contains(line, "=") {
			continue
		}
		found = true
		parts := strings.SplitN(line, "=", 2)
		key := strings.TrimSpace(parts[0])
		val := strings.Trim(strings.TrimSpace(parts[1]), `"`)
		switch key {
		case "cc":
			out.CC = val
		case "include":
			out.Include = val
		case "pic":
			out.PIC = val == "true"
		case "tls_model":
			out.TLS = val
		}
	}
	if !found {
		return cgoWant{}, fmt.Errorf("no section %q in %s", wantSection, path)
	}
	return out, nil
}

func sectionsAligned(a, b cgoWant) bool {
	return a.CC == b.CC && a.Include == b.Include && a.PIC == b.PIC
}

func envMatches(envText string, want cgoWant) bool {
	if !strings.Contains(envText, "CC="+want.CC) {
		return false
	}
	if want.Include != "" && !strings.Contains(envText, want.Include) {
		return false
	}
	if want.PIC {
		if !strings.Contains(envText, "-fPIC") {
			return false
		}
	}
	if want.CC != "musl-gcc" && strings.Contains(envText, "musl-gcc") {
		return false
	}
	return true
}
