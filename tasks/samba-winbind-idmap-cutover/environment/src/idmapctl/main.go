package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"syscall"
)

type principal struct {
	Name  string `json:"name"`
	SID   string `json:"sid"`
	UID   int    `json:"uid"`
	GID   int    `json:"gid"`
	Range string `json:"range"`
}

type report struct {
	Status     string       `json:"status"`
	Backend    string       `json:"backend"`
	SealGen    string       `json:"seal_gen"`
	Principals []principal  `json:"principals"`
}

func mustRead(path string) string {
	b, err := os.ReadFile(path)
	if err != nil {
		fatal("read %s: %v", path, err)
	}
	return strings.TrimSpace(string(b))
}

func fatal(format string, args ...any) {
	fmt.Fprintf(os.Stderr, "idmapctl: "+format+"\n", args...)
	os.Exit(1)
}

func loadEnvFile(path string) map[string]string {
	out := map[string]string{}
	f, err := os.Open(path)
	if err != nil {
		return out
	}
	defer f.Close()
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		k, v, ok := strings.Cut(line, "=")
		if !ok {
			continue
		}
		out[strings.TrimSpace(k)] = strings.TrimSpace(v)
	}
	return out
}

func loadRoster(path string) []struct {
	name, sid string
	lo, hi, uid int
} {
	f, err := os.Open(path)
	if err != nil {
		fatal("roster: %v", err)
	}
	defer f.Close()
	var rows []struct {
		name, sid string
		lo, hi, uid int
	}
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		parts := strings.Fields(line)
		if len(parts) < 5 {
			continue
		}
		lo, _ := strconv.Atoi(parts[2])
		hi, _ := strconv.Atoi(parts[3])
		uid, _ := strconv.Atoi(parts[4])
		rows = append(rows, struct {
			name, sid string
			lo, hi, uid int
		}{parts[0], parts[1], lo, hi, uid})
	}
	return rows
}

func sameInode(a, b string) bool {
	var sa, sb syscall.Stat_t
	if err := syscall.Stat(a, &sa); err != nil {
		return false
	}
	if err := syscall.Stat(b, &sb); err != nil {
		return false
	}
	return sa.Ino == sb.Ino && sa.Dev == sb.Dev
}

func main() {
	etc := getenv("SAMBA_ETC", "/etc/samba")
	root := getenv("SAMBA_VAR", "/var/lib/samba")
	rosterPath := getenv("IDMAP_ROSTER", filepath.Join(etc, "idmap.roster"))
	tdbPath := getenv("IDMAP_TDB", filepath.Join(root, "idmap.tdb"))
	reportPath := getenv("IDMAP_REPORT", "/output/idmap-cutover.json")
	sealPath := getenv("DESK_SEAL", filepath.Join(etc, "desk.seal"))
	envPath := getenv("SAMBA_DESKD_ENV", filepath.Join(etc, "deskd.env"))

	meta := filepath.Join(root, "meta")
	attach := filepath.Join(root, "attach")
	origins := filepath.Join(root, "origins")

	if _, err := os.Stat(filepath.Join(meta, "pref.armed")); err != nil {
		fatal("preference not armed")
	}
	mode := mustRead(filepath.Join(meta, "pref.mode"))
	if mode != "equality-inclusive" {
		fatal("pref mode %q", mode)
	}

	seal := mustRead(sealPath)
	if mustRead(filepath.Join(meta, "pref.armed")) != seal {
		fatal("pref.armed must equal desk.seal")
	}
	if mustRead(filepath.Join(meta, "tip.ok")) != seal {
		fatal("tip.ok must equal desk.seal")
	}
	genLive := mustRead(filepath.Join(meta, "gen.live"))
	if genLive != seal {
		fatal("gen.live %q != seal %q", genLive, seal)
	}
	if _, err := os.Stat(filepath.Join(meta, "cutover.ok")); err != nil {
		fatal("missing cutover.ok")
	}
	intent := mustRead(filepath.Join(meta, "attach.intent"))
	if intent != "seal" {
		fatal("attach.intent %q", intent)
	}

	env := loadEnvFile(envPath)
	if env["PAYLOAD_LINEAGE"] != "sealed" {
		fatal("PAYLOAD_LINEAGE=%q", env["PAYLOAD_LINEAGE"])
	}
	hold := strings.TrimSpace(env["HOLD_TOKEN"])
	if hold == "" {
		fatal("missing HOLD_TOKEN")
	}

	backend := mustRead(filepath.Join(meta, "backends.toml"))
	// backends.toml is key=value lines; kn=...
	kn := ""
	for _, line := range strings.Split(backend, "\n") {
		line = strings.TrimSpace(line)
		if strings.HasPrefix(line, "kn=") {
			kn = strings.TrimPrefix(line, "kn=")
		}
	}
	if kn == "" || kn == "hash" || kn == "rid" || kn == "unset" {
		fatal("backend kn %q rejected", kn)
	}

	roster := loadRoster(rosterPath)
	if len(roster) == 0 {
		fatal("empty roster")
	}

	var principals []principal
	var tdbLines []string
	for _, r := range roster {
		mapPath := filepath.Join(attach, r.name+".bin")
		sealed := filepath.Join(origins, r.name, "sealed", "map.bin")
		if !sameInode(mapPath, sealed) {
			fatal("attach %s not same-inode as sealed shelf", r.name)
		}
		raw := mustRead(mapPath)
		parts := strings.Fields(raw)
		if len(parts) < 3 {
			fatal("bad map for %s", r.name)
		}
		uid, _ := strconv.Atoi(parts[1])
		gid, _ := strconv.Atoi(parts[2])
		if parts[0] != r.sid || uid != r.uid || gid != r.uid {
			fatal("map mismatch for %s", r.name)
		}
		if uid < r.lo || uid > r.hi {
			fatal("uid out of range for %s", r.name)
		}
		principals = append(principals, principal{
			Name: r.name, SID: r.sid, UID: uid, GID: gid,
			Range: fmt.Sprintf("%d-%d", r.lo, r.hi),
		})
		tdbLines = append(tdbLines, fmt.Sprintf("%s %d %d", r.sid, uid, gid))
	}

	if err := os.MkdirAll(filepath.Dir(reportPath), 0o755); err != nil {
		fatal("mkdir report: %v", err)
	}
	if err := os.MkdirAll(filepath.Dir(tdbPath), 0o755); err != nil {
		fatal("mkdir tdb: %v", err)
	}
	if err := os.WriteFile(tdbPath, []byte(strings.Join(tdbLines, "\n")+"\n"), 0o644); err != nil {
		fatal("write tdb: %v", err)
	}

	rep := report{Status: "ok", Backend: kn, SealGen: seal, Principals: principals}
	blob, err := json.MarshalIndent(rep, "", "  ")
	if err != nil {
		fatal("json: %v", err)
	}
	if err := os.WriteFile(reportPath, append(blob, '\n'), 0o644); err != nil {
		fatal("write report: %v", err)
	}

	// Publish durable arm markers used by reload.
	_ = os.WriteFile(filepath.Join(meta, "cut.arm"), []byte(seal+"\n"), 0o644)
	_ = os.WriteFile(filepath.Join(meta, "active.kn"), []byte(kn+"\n"), 0o644)
}

func getenv(k, def string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return def
}
