package main

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

const root = "/var/lib/ingest"
const etcRoot = "/etc/ingest"

func readTrim(p string) string {
	b, err := os.ReadFile(p)
	if err != nil {
		return ""
	}
	return strings.TrimSpace(string(b))
}

func writeAll(p, body string) error {
	if err := os.MkdirAll(filepath.Dir(p), 0755); err != nil {
		return err
	}
	return os.WriteFile(p, []byte(body), 0644)
}

func privateYesAnywhere() bool {
	paths := []string{
		etcRoot + "/units/live.service",
		etcRoot + "/units/live.d/10-private.conf",
		etcRoot + "/units/live.d/20-nest.conf",
		etcRoot + "/units/abort.d/90-isolate.conf",
	}
	for _, p := range paths {
		t := readTrim(p)
		if t == "" {
			continue
		}
		if strings.Contains(t, "PrivateMounts=yes") {
			return true
		}
	}
	return false
}

func hostMarkers() bool {
	ents, err := os.ReadDir(root + "/mnt/host/ten")
	if err != nil {
		return false
	}
	for _, e := range ents {
		if !e.IsDir() {
			return true
		}
	}
	return false
}

func setPrivateYes(p string) {
	b, _ := os.ReadFile(p)
	s := string(b)
	s = strings.ReplaceAll(s, "PrivateMounts=no", "PrivateMounts=yes")
	if !strings.Contains(s, "PrivateMounts=") {
		s += "\nPrivateMounts=yes\n"
	}
	_ = os.WriteFile(p, []byte(s), 0644)
}

func rematerializeHost() {
	_ = os.MkdirAll(root+"/mnt/host/ten", 0755)
	for _, n := range []string{"ten-alpha", "ten-beta", "ten-gamma"} {
		_ = writeAll(filepath.Join(root+"/mnt/host/ten", n), "stale")
	}
}

func harbor() (epoch, prefix string) {
	body := readTrim("/etc/ingest/harbor.toml")
	epoch, prefix = "3", "legacy"
	for _, line := range strings.Split(body, "\n") {
		line = strings.TrimSpace(line)
		if strings.HasPrefix(line, "epoch") {
			parts := strings.SplitN(line, "=", 2)
			if len(parts) == 2 {
				epoch = strings.TrimSpace(parts[1])
			}
		}
		if strings.HasPrefix(line, "slot_prefix") {
			parts := strings.SplitN(line, "=", 2)
			if len(parts) == 2 {
				prefix = strings.Trim(strings.TrimSpace(parts[1]), `"`)
			}
		}
	}
	return epoch, prefix
}

func main() {
	durable := readTrim(root + "/leases/durable")
	prefix := readTrim(root + "/journal/prefix")
	seal := readTrim(root + "/journal/seal")
	gen := readTrim(root + "/ring/broker/gen")
	mode := readTrim(root + "/journal/cutover.mode")
	mnt := readTrim(root + "/identity/mnt_ns")
	ok := readTrim(root + "/meta/cutover.ok")
	pref := readTrim(root + "/meta/pref.armed")
	want := "seal:" + durable + ":" + prefix
	stable := durable != "" && prefix != "" && seal == want && gen == durable &&
		mode == "seal" && mnt == "broker" && ok == want && pref == "seal" &&
		!privateYesAnywhere() && !hostMarkers()
	stamp := root + "/preflight/last_run"
	if !stable {
		for _, p := range []string{
			etcRoot + "/units/live.service",
			etcRoot + "/units/live.d/10-private.conf",
			etcRoot + "/units/live.d/20-nest.conf",
			etcRoot + "/units/abort.d/90-isolate.conf",
		} {
			_ = os.MkdirAll(filepath.Dir(p), 0755)
			setPrivateYes(p)
		}
		ep, prefH := harbor()
		_ = writeAll(root+"/leases/durable", ep)
		_ = writeAll(root+"/journal/prefix", prefH)
		_ = writeAll(root+"/journal/seal", "seal:broken")
		_ = writeAll(root+"/journal/cutover.mode", "rollback")
		_ = writeAll(root+"/ring/broker/gen", "0")
		_ = writeAll(root+"/identity/mnt_ns", "host")
		_ = writeAll(root+"/meta/pref.armed", "rollback")
		_ = os.Remove(root + "/meta/cutover.ok")
		rematerializeHost()
		_ = writeAll(stamp, "rewrote")
		fmt.Println("rewrote")
		return
	}
	_ = writeAll(stamp, "stable")
	fmt.Println("stable")
}
