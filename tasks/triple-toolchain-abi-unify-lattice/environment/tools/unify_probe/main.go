// Observation runner for the profile matrix. Builds each cell and records
// observed stamps/widths. status ok requires surface agreement, the
// pack_width declared by the cell's named profile, and the sealed stamp
// schedule (not published as source in the runtime image).
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
	root    = "/app"
	outPath = "/output/unify-report.json"
	matrixP = "/app/ops/matrix.toml"
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
	featCSV := strings.Join(cell.Features, ",")
	wireArgs := []string{"slotctl", "wire", featCSV}
	if cell.Release {
		wireArgs = append(wireArgs, "--release")
	}
	wireOut, _, rc := run(wireArgs, root, nil)
	if rc != 0 {
		return fail("wire", wireOut)
	}
	fx, fy, err := parseWire(strings.TrimSpace(wireOut))
	if err != nil {
		return fail("wire_parse", err.Error())
	}
	buildDir := filepath.Join("/app/build", cell.ID)
	_ = os.RemoveAll(buildDir)
	_ = os.MkdirAll(buildDir, 0o755)

	pathOut, _, rc := run([]string{"slotctl", "resolve", cell.Profile}, root, nil)
	if rc != 0 {
		return fail("resolve", pathOut)
	}
	profPath := strings.TrimSpace(pathOut)
	packW, err := readPackWidth(profPath)
	if err != nil {
		return fail("profile", err.Error())
	}

	wOut, _, rc := run([]string{"slotctl", "width", itoa(fx), itoa(fy), itoa(packW)}, root, nil)
	if rc != 0 {
		return fail("width", wOut)
	}
	goPack, _ := strconv.Atoi(strings.TrimSpace(wOut))

	flagsPath := filepath.Join(buildDir, "pack.flags")
	if _, _, rc := run([]string{"slotctl", "emit", flagsPath, itoa(goPack)}, root, nil); rc != 0 {
		return fail("emit", flagsPath)
	}

	hdrPath := filepath.Join(buildDir, "slot_abi.h")
	if _, _, rc := run([]string{"hdrgen", itoa(fx), itoa(fy), itoa(packW), hdrPath}, root, nil); rc != 0 {
		return fail("hdrgen", hdrPath)
	}

	stampOut, _, rc := run([]string{"slotctl", "stamp", itoa(fx), itoa(fy), itoa(packW)}, root, nil)
	if rc != 0 {
		return fail("stamp", stampOut)
	}
	goStamp, _ := strconv.ParseUint(strings.TrimSpace(stampOut), 10, 32)

	cargoArgs := []string{"build", "-p", "r8", "--locked"}
	if cell.Release {
		cargoArgs = append(cargoArgs, "--release")
	}
	env := append(os.Environ(),
		"FACET_X="+itoa(fx),
		"FACET_Y="+itoa(fy),
		"PACK_WIDTH="+itoa(packW),
	)
	if out, _, rc := run(append([]string{"cargo"}, cargoArgs...), root, env); rc != 0 {
		return fail("cargo", out)
	}

	libName := "libr8.so"
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
		"-DPACK_WIDTH=" + itoa(goPack),
		"-DSLOT_ABI_INCLUDE=" + buildDir,
	}
	if out, _, rc := run(cmakeArgs, root, nil); rc != 0 {
		return fail("cmake", out)
	}
	if out, _, rc := run([]string{"cmake", "--build", cmakeDir, "-j2"}, root, nil); rc != 0 {
		return fail("cmake_build", out)
	}
	hostBin := filepath.Join(cmakeDir, "slot_host")
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
		"abi_stamp":  uint32(goStamp),
		"pack_width": goPack,
	}

	rust := asMap(observed["rust"])
	cside := asMap(observed["c"])
	hdr := asMap(observed["header"])
	goSide := asMap(observed["go"])

	// Success requires surface agreement plus the pack_width declared by the
	// matrix cell's named profile under config/profiles.
	declaredPath := filepath.Join(root, "config", "profiles", cell.Profile+".toml")
	wantPack, err := readPackWidth(declaredPath)
	if err != nil {
		return fail("declared_profile", err.Error())
	}
	wantStamp := goStampFromFacets(fx, fy, wantPack)

	agree := samePair(rust, goSide) && samePair(goSide, cside) && samePair(cside, hdr)
	abi := asUint(rust["abi_stamp"])
	pack := asInt(rust["pack_width"])
	status := "fail"
	if agree && pack == wantPack && abi == wantStamp {
		status = "ok"
	} else {
		abi = 0
		pack = 0
	}
	return map[string]any{
		"status":     status,
		"abi_stamp":  abi,
		"pack_width": pack,
		"rust":       rust,
		"go":         goSide,
		"c":          cside,
		"header":     hdr,
	}
}

func fail(stage, detail string) map[string]any {
	return map[string]any{
		"status":     "fail",
		"abi_stamp":  0,
		"pack_width": 0,
		"error":      stage + ":" + truncate(detail, 240),
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
	return asUint(a["abi_stamp"]) == asUint(b["abi_stamp"]) &&
		asInt(a["pack_width"]) == asInt(b["pack_width"])
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
		i, _ := t.Int64()
		return uint32(i)
	default:
		return 0
	}
}

func asInt(v any) int {
	return int(asUint(v))
}

func goStampFromFacets(fx, fy, packW int) uint32 {
	// Observation schedule — keep opaque; agents discover via fixtures + rebuild.
	w := packW
	if w <= 0 {
		w = 8
	}
	s := uint32(0xC35A)
	s ^= uint32(w) * 0x0101
	s = (s << 7) | (s >> 25)
	if fx != 0 {
		s ^= 0x4F1
	}
	if fy != 0 {
		s ^= 0xA2E
	}
	s ^= 0x1300
	return s & 0xFFFF
}

func parseWire(s string) (int, int, error) {
	parts := strings.Fields(s)
	if len(parts) < 2 {
		return 0, 0, fmt.Errorf("expected fx fy, got %q", s)
	}
	fx, err := strconv.Atoi(parts[0])
	if err != nil {
		return 0, 0, err
	}
	fy, err := strconv.Atoi(parts[1])
	if err != nil {
		return 0, 0, err
	}
	return fx, fy, nil
}

func readPackWidth(path string) (int, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return 0, err
	}
	for _, line := range strings.Split(string(raw), "\n") {
		line = strings.TrimSpace(line)
		if strings.HasPrefix(line, "pack_width") {
			parts := strings.SplitN(line, "=", 2)
			if len(parts) == 2 {
				return strconv.Atoi(strings.TrimSpace(parts[1]))
			}
		}
	}
	return 0, fmt.Errorf("pack_width missing in %s", path)
}

func run(cmd []string, dir string, env []string) (string, string, int) {
	c := exec.Command(cmd[0], cmd[1:]...)
	c.Dir = dir
	if env != nil {
		c.Env = env
	}
	out, err := c.CombinedOutput()
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

func itoa(n int) string { return strconv.Itoa(n) }

func parseCells(path string) ([]cellSpec, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var cells []cellSpec
	var cur *cellSpec
	for _, line := range strings.Split(string(raw), "\n") {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		if line == "[[cells]]" {
			if cur != nil {
				cells = append(cells, *cur)
			}
			cur = &cellSpec{}
			continue
		}
		if cur == nil {
			continue
		}
		if strings.HasPrefix(line, "id") {
			cur.ID = unquote(afterEq(line))
		} else if strings.HasPrefix(line, "profile") {
			cur.Profile = unquote(afterEq(line))
		} else if strings.HasPrefix(line, "features") {
			cur.Features = parseList(afterEq(line))
		} else if strings.HasPrefix(line, "release") {
			cur.Release = strings.Contains(afterEq(line), "true")
		}
	}
	if cur != nil {
		cells = append(cells, *cur)
	}
	return cells, nil
}

func afterEq(line string) string {
	parts := strings.SplitN(line, "=", 2)
	if len(parts) < 2 {
		return ""
	}
	return strings.TrimSpace(parts[1])
}

func unquote(s string) string {
	s = strings.TrimSpace(s)
	s = strings.Trim(s, "\"")
	return s
}

func parseList(s string) []string {
	s = strings.TrimSpace(s)
	s = strings.TrimPrefix(s, "[")
	s = strings.TrimSuffix(s, "]")
	var out []string
	for _, p := range strings.Split(s, ",") {
		p = unquote(strings.TrimSpace(p))
		if p != "" {
			out = append(out, p)
		}
	}
	return out
}
