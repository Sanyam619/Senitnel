// Observation runner for the profile matrix. Builds each cell and records
// observed digests/epochs/members. status ok requires surface agreement plus
// the bitcode_epoch and archive_members declared by the cell's named profile,
// with vis_digest matching the strand+epoch+members schedule.
package main

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
)

const (
	root     = "/app"
	outPath  = "/output/lattice-report.json"
	matrixP  = "/app/ops/matrix.toml"
	archctl  = "/app/bin/archctl"
	visgen   = "/app/bin/visgen"
	cargoBin = "cargo"
)

type cellSpec struct {
	ID       string
	Profile  string
	Features []string
	Release  bool
}

func main() {
	cells, err := parseCells(matrixP)
	if err != nil {
		fmt.Fprintf(os.Stderr, "matrix: %v\n", err)
		os.Exit(2)
	}
	_ = os.MkdirAll("/app/build", 0o755)
	report := map[string]any{"cells": map[string]any{}}
	cellsOut := report["cells"].(map[string]any)

	for _, cell := range cells {
		cellsOut[cell.ID] = runCell(cell)
	}

	_ = os.MkdirAll(filepath.Dir(outPath), 0o755)
	enc, _ := json.MarshalIndent(report, "", "  ")
	if err := os.WriteFile(outPath, append(enc, '\n'), 0o644); err != nil {
		fmt.Fprintf(os.Stderr, "write: %v\n", err)
		os.Exit(2)
	}
	fmt.Printf("wrote %s\n", outPath)
}

func runCell(cell cellSpec) map[string]any {
	sa, sb := 0, 0
	for _, f := range cell.Features {
		switch f {
		case "strand_a":
			sa = 1
		case "strand_b":
			sb = 1
		}
	}
	buildDir := filepath.Join("/app/build", cell.ID)
	_ = os.RemoveAll(buildDir)
	_ = os.MkdirAll(buildDir, 0o755)

	pathOut, _, rc := run([]string{archctl, "resolve", cell.Profile}, root, nil)
	if rc != 0 {
		return fail("resolve", pathOut)
	}
	profPath := strings.TrimSpace(pathOut)
	epoch, members, err := readProfile(profPath)
	if err != nil {
		return fail("profile", err.Error())
	}

	mOut, _, rc := run([]string{archctl, "members", itoa(sa), itoa(sb), itoa(members)}, root, nil)
	if rc != 0 {
		return fail("members", mOut)
	}
	goMembers, _ := strconv.Atoi(strings.TrimSpace(mOut))

	flagsPath := filepath.Join(buildDir, "pack.flags")
	if _, _, rc := run([]string{archctl, "emit", flagsPath, itoa(goMembers)}, root, nil); rc != 0 {
		return fail("emit", flagsPath)
	}

	hdrPath := filepath.Join(buildDir, "slot_vis.h")
	if _, _, rc := run([]string{visgen, itoa(sa), itoa(sb), itoa(epoch), itoa(goMembers), hdrPath}, root, nil); rc != 0 {
		return fail("visgen", hdrPath)
	}

	digOut, _, rc := run([]string{archctl, "digest", itoa(sa), itoa(sb), itoa(epoch), itoa(goMembers)}, root, nil)
	if rc != 0 {
		return fail("digest", digOut)
	}
	goDig, _ := strconv.ParseUint(strings.TrimSpace(digOut), 10, 32)

	cargoArgs := []string{"build", "-p", "r7", "--locked"}
	if cell.Release {
		cargoArgs = append(cargoArgs, "--release")
	}
	rel := "0"
	if cell.Release {
		rel = "1"
	}
	env := append(os.Environ(),
		"STRAND_A="+itoa(sa),
		"STRAND_B="+itoa(sb),
		"BITCODE_EPOCH="+itoa(epoch),
		"ARCHIVE_MEMBERS="+itoa(goMembers),
		"CELL_RELEASE="+rel,
	)
	_ = os.RemoveAll(filepath.Join(root, "target"))
	if out, _, rc := run(append([]string{cargoBin}, cargoArgs...), root, env); rc != 0 {
		return fail("cargo", out)
	}

	libName := "libr7.so"
	libSrc := filepath.Join(root, "target", "debug", libName)
	if cell.Release {
		libSrc = filepath.Join(root, "target", "release", libName)
	}
	libDst := filepath.Join(buildDir, libName)
	if out, _, rc := run([]string{"cp", libSrc, libDst}, root, nil); rc != 0 {
		return fail("copy_lib", out)
	}

	cmakeDir := filepath.Join(buildDir, "cmake")
	_ = os.MkdirAll(cmakeDir, 0o755)
	cmakeArgs := []string{
		"cmake", "-S", filepath.Join(root, "host"), "-B", cmakeDir,
		"-DARCHIVE_MEMBERS=" + itoa(goMembers),
		"-DSLOT_VIS_INCLUDE=" + buildDir,
	}
	if out, _, rc := run(cmakeArgs, root, nil); rc != 0 {
		return fail("cmake", out)
	}
	if out, _, rc := run([]string{"cmake", "--build", cmakeDir, "-j2"}, root, nil); rc != 0 {
		return fail("cmake_build", out)
	}
	hostBin := filepath.Join(cmakeDir, "lattice_host")
	hostOut, _, rc := run([]string{hostBin, libDst}, buildDir, []string{
		"LD_LIBRARY_PATH=" + buildDir,
	})
	if rc != 0 {
		return fail("host", hostOut)
	}

	var observed map[string]any
	if err := json.Unmarshal([]byte(strings.TrimSpace(hostOut)), &observed); err != nil {
		return fail("parse_host", hostOut)
	}
	observed["go"] = map[string]any{
		"vis_digest":      uint32(goDig),
		"bitcode_epoch":   epoch,
		"archive_members": goMembers,
	}

	rust := asMap(observed["rust"])
	cside := asMap(observed["c"])
	hdr := asMap(observed["header"])
	goSide := asMap(observed["go"])

	declaredPath := filepath.Join(root, "config", "profiles", cell.Profile+".toml")
	wantEpoch, wantMembers, err := readProfile(declaredPath)
	if err != nil {
		return fail("declared_profile", err.Error())
	}
	wantDig := auditDigest(sa, sb, wantEpoch, wantMembers)

	agree := sameTriple(rust, goSide) && sameTriple(goSide, cside) && samePair(cside, hdr)
	dig := asUint(rust["vis_digest"])
	ep := asInt(rust["bitcode_epoch"])
	mem := asInt(goSide["archive_members"])
	status := "fail"
	if agree && ep == wantEpoch && dig == wantDig && mem == wantMembers {
		status = "ok"
	} else {
		dig = 0
		ep = 0
		mem = 0
	}
	return map[string]any{
		"status":          status,
		"vis_digest":      dig,
		"bitcode_epoch":   ep,
		"archive_members": mem,
		"rust":            rust,
		"go":              goSide,
		"c":               cside,
		"header":          hdr,
	}
}

func fail(stage, detail string) map[string]any {
	return map[string]any{
		"status":          "fail",
		"vis_digest":      0,
		"bitcode_epoch":   0,
		"archive_members": 0,
		"error":           stage + ":" + truncate(detail, 240),
	}
}

func truncate(s string, n int) string {
	s = strings.TrimSpace(s)
	if len(s) <= n {
		return s
	}
	return s[:n]
}

func samePair(a, b map[string]any) bool {
	return asUint(a["vis_digest"]) == asUint(b["vis_digest"]) &&
		asInt(a["bitcode_epoch"]) == asInt(b["bitcode_epoch"])
}

func sameTriple(a, b map[string]any) bool {
	if !samePair(a, b) {
		return false
	}
	_, aHas := a["archive_members"]
	_, bHas := b["archive_members"]
	if aHas && bHas {
		return asInt(a["archive_members"]) == asInt(b["archive_members"])
	}
	return true
}

func auditDigest(a, b, e, m int) uint32 {
	epoch := uint32(e)
	if epoch == 0 {
		epoch = 3
	}
	members := uint32(m)
	if members == 0 {
		members = 4
	}
	s := uint32(0xA7E3)
	s ^= epoch * 0x1051
	s = (s << 7) | (s >> 25)
	s ^= (members + 1) * 0x21B
	s = (s << 11) | (s >> 21)
	if a != 0 {
		s ^= 0x8C5
	}
	if b != 0 {
		s ^= 0xD2F
	}
	s ^= 0x4400
	return s & 0xFFFF
}

func readProfile(path string) (epoch int, members int, err error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return 0, 0, err
	}
	epoch, members = -1, -1
	for _, line := range strings.Split(string(data), "\n") {
		line = strings.TrimSpace(line)
		if strings.HasPrefix(line, "bitcode_epoch") {
			parts := strings.SplitN(line, "=", 2)
			if len(parts) == 2 {
				epoch, _ = strconv.Atoi(strings.TrimSpace(parts[1]))
			}
		}
		if strings.HasPrefix(line, "archive_members") {
			parts := strings.SplitN(line, "=", 2)
			if len(parts) == 2 {
				members, _ = strconv.Atoi(strings.TrimSpace(parts[1]))
			}
		}
	}
	if epoch < 0 || members < 0 {
		return 0, 0, fmt.Errorf("incomplete profile %s", path)
	}
	return epoch, members, nil
}

func parseCells(path string) ([]cellSpec, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var cells []cellSpec
	var cur *cellSpec
	for _, raw := range strings.Split(string(data), "\n") {
		line := strings.TrimSpace(raw)
		if line == "[[cells]]" {
			if cur != nil {
				cells = append(cells, *cur)
			}
			cur = &cellSpec{}
			continue
		}
		if cur == nil || line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		parts := strings.SplitN(line, "=", 2)
		if len(parts) != 2 {
			continue
		}
		key := strings.TrimSpace(parts[0])
		val := strings.TrimSpace(parts[1])
		switch key {
		case "id":
			cur.ID = strings.Trim(val, `"`)
		case "profile":
			cur.Profile = strings.Trim(val, `"`)
		case "release":
			cur.Release = val == "true"
		case "features":
			rest := val
			for {
				i := strings.IndexByte(rest, '"')
				if i < 0 {
					break
				}
				rest = rest[i+1:]
				j := strings.IndexByte(rest, '"')
				if j < 0 {
					break
				}
				f := rest[:j]
				rest = rest[j+1:]
				if f != "" {
					cur.Features = append(cur.Features, f)
				}
			}
		}
	}
	if cur != nil {
		cells = append(cells, *cur)
	}
	return cells, nil
}

func run(args []string, dir string, env []string) (string, string, int) {
	cmd := exec.Command(args[0], args[1:]...)
	cmd.Dir = dir
	if env != nil {
		cmd.Env = env
	}
	out, err := cmd.CombinedOutput()
	rc := 0
	if err != nil {
		if ee, ok := err.(*exec.ExitError); ok {
			rc = ee.ExitCode()
		} else {
			rc = 1
		}
	}
	return string(out), "", rc
}

func asMap(v any) map[string]any {
	if m, ok := v.(map[string]any); ok {
		return m
	}
	return map[string]any{}
}

func asUint(v any) uint32 {
	switch t := v.(type) {
	case float64:
		return uint32(t)
	case int:
		return uint32(t)
	case uint32:
		return t
	case json.Number:
		n, _ := t.Int64()
		return uint32(n)
	default:
		return 0
	}
}

func asInt(v any) int {
	switch t := v.(type) {
	case float64:
		return int(t)
	case int:
		return t
	case json.Number:
		n, _ := t.Int64()
		return int(n)
	default:
		return 0
	}
}

func itoa(n int) string {
	return strconv.Itoa(n)
}
