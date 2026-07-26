package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
)

const (
	root     = "/var/lib/ingest"
	etcRoot  = "/etc/ingest"
	outPath  = "/output/lease-cutover.json"
	sealCap  = "/etc/ingest/fleet.seal"
	walPath  = "/var/lib/ingest/journal/act.wal"
)

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

type tip struct {
	gen, seq       int
	epoch, prefix  string
	mode           string
}

func sealedTip() (tip, error) {
	capBody := readTrim(sealCap)
	cap := 0
	for _, line := range strings.Split(capBody, "\n") {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		n, err := strconv.Atoi(line)
		if err != nil {
			return tip{}, fmt.Errorf("bad seal cap")
		}
		cap = n
		break
	}
	body, err := os.ReadFile(walPath)
	if err != nil {
		return tip{}, err
	}
	var best *tip
	for _, line := range strings.Split(string(body), "\n") {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		parts := strings.Split(line, "|")
		if len(parts) < 5 {
			continue
		}
		gen, err1 := strconv.Atoi(parts[0])
		seq, err2 := strconv.Atoi(parts[1])
		if err1 != nil || err2 != nil {
			continue
		}
		if gen > cap {
			continue
		}
		t := tip{gen: gen, seq: seq, epoch: parts[2], prefix: parts[3], mode: parts[4]}
		if best == nil || t.gen > best.gen || (t.gen == best.gen && t.seq > best.seq) {
			cp := t
			best = &cp
		}
	}
	if best == nil {
		return tip{}, fmt.Errorf("no sealed tip")
	}
	return *best, nil
}

func privateOpen() bool {
	paths := []string{
		etcRoot + "/units/live.service",
		etcRoot + "/units/live.d/10-private.conf",
		etcRoot + "/units/live.d/20-nest.conf",
		etcRoot + "/units/abort.d/90-isolate.conf",
	}
	for _, p := range paths {
		t := readTrim(p)
		if t == "" && strings.Contains(p, "abort.d") {
			continue
		}
		if strings.Contains(t, "PrivateMounts=yes") {
			return false
		}
		if !strings.Contains(t, "PrivateMounts=no") {
			return false
		}
	}
	return true
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

func prefSealed() bool {
	return readTrim(root+"/meta/pref.armed") == "seal"
}

func roster() []string {
	b := readTrim(etcRoot + "/tenant.roster")
	var out []string
	for _, line := range strings.Split(b, "\n") {
		line = strings.TrimSpace(line)
		if line != "" && !strings.HasPrefix(line, "#") {
			out = append(out, line)
		}
	}
	sort.Strings(out)
	return out
}

func main() {
	want, err := sealedTip()
	if err != nil {
		fmt.Fprintf(os.Stderr, "ringfan: %v\n", err)
		os.Exit(1)
	}
	if want.mode != "seal" {
		fmt.Fprintf(os.Stderr, "ringfan: sealed tip mode is not seal\n")
		os.Exit(1)
	}
	mode := readTrim(root + "/journal/cutover.mode")
	if mode != "seal" {
		fmt.Fprintf(os.Stderr, "ringfan: cutover.mode must be seal (got %q)\n", mode)
		os.Exit(1)
	}
	durable := readTrim(root + "/leases/durable")
	pref := readTrim(root + "/journal/prefix")
	seal := readTrim(root + "/journal/seal")
	tipSeal := "seal:" + want.epoch + ":" + want.prefix
	if durable != want.epoch || pref != want.prefix || seal != tipSeal {
		fmt.Fprintf(os.Stderr, "ringfan: durable plane mismatch sealed tip\n")
		os.Exit(1)
	}
	if !prefSealed() {
		fmt.Fprintf(os.Stderr, "ringfan: preference plane not seal-bound\n")
		os.Exit(1)
	}
	if !privateOpen() {
		fmt.Fprintf(os.Stderr, "ringfan: unit isolation still active\n")
		os.Exit(1)
	}
	arm := readTrim(root + "/meta/seal_gen.arm")
	if arm != want.epoch {
		fmt.Fprintf(os.Stderr, "ringfan: seal_gen.arm not armed to sealed epoch\n")
		os.Exit(1)
	}
	ok := readTrim(root + "/meta/cutover.ok")
	if ok != tipSeal {
		fmt.Fprintf(os.Stderr, "ringfan: cutover receipt missing or stale\n")
		os.Exit(1)
	}
	if readTrim(root+"/identity/mnt_ns") != "broker" || hostMarkers() {
		fmt.Fprintf(os.Stderr, "ringfan: broker seating incomplete\n")
		os.Exit(1)
	}
	names := roster()
	if len(names) == 0 {
		fmt.Fprintf(os.Stderr, "ringfan: empty roster\n")
		os.Exit(1)
	}
	brokerTen := root + "/mnt/broker/ten"
	for _, name := range names {
		if _, err := os.Stat(filepath.Join(brokerTen, name)); err != nil {
			fmt.Fprintf(os.Stderr, "ringfan: missing broker marker %s\n", name)
			os.Exit(1)
		}
	}

	slotsDir := root + "/ring/broker/slots"
	_ = os.MkdirAll(slotsDir, 0755)
	for _, name := range names {
		slot := want.prefix + ":" + name + ":" + want.epoch
		if err := writeAll(filepath.Join(slotsDir, name), slot); err != nil {
			fmt.Fprintf(os.Stderr, "ringfan: %v\n", err)
			os.Exit(1)
		}
	}
	_ = writeAll(root+"/ring/broker/gen", want.epoch)

	var tips []string
	for _, name := range names {
		tips = append(tips, name+"="+want.prefix+":"+name+":"+want.epoch)
	}
	_ = writeAll(root+"/meta/activation.toml", "[tips]\n"+strings.Join(tips, "\n")+"\n")

	type row struct {
		Tenant          string `json:"tenant"`
		BufSlot         string `json:"buf_slot"`
		MountNS         string `json:"mount_ns"`
		LeaseEpoch      int    `json:"lease_epoch"`
		BufFresh        bool   `json:"buf_fresh"`
		PreflightStable bool   `json:"preflight_stable"`
	}
	ep := 0
	fmt.Sscanf(want.epoch, "%d", &ep)
	var tenants []row
	for _, name := range names {
		tenants = append(tenants, row{
			Tenant: name, BufSlot: want.prefix + ":" + name + ":" + want.epoch,
			MountNS: "broker", LeaseEpoch: ep, BufFresh: true, PreflightStable: true,
		})
	}
	payload := map[string]any{"version": 1, "tenants": tenants}
	raw, _ := json.MarshalIndent(payload, "", "  ")
	_ = writeAll(outPath, string(raw)+"\n")
	fmt.Println("ok")
}
