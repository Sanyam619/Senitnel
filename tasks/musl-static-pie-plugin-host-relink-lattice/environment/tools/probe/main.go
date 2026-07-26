// Observation runner for the profile matrix. Builds each cell and records
// host/supervisor JSON outcomes; it does not decide toolchain stamp policy.
package main

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

const (
	root            = "/app"
	outPath         = "/output/lattice-report.json"
	matrixP         = "/app/ops/matrix.toml"
	contract        = "/app/link/contract.toml"
	defaultSafePath = "/usr/local/cargo/bin:/usr/local/go/bin:/usr/bin:/bin"
)

type cellSpec struct {
	ID       string
	Lane     string
	Profile  string
	Features []string
	Role     string
	Release  bool
}

func main() {
	cells, err := parseCells(matrixP)
	if err != nil {
		fmt.Fprintf(os.Stderr, "matrix: %v\n", err)
		os.Exit(2)
	}
	exp, err := parseContract(contract)
	if err != nil {
		fmt.Fprintf(os.Stderr, "contract: %v\n", err)
		os.Exit(2)
	}
	_ = os.MkdirAll("/app/build", 0o755)
	report := map[string]any{"cells": map[string]any{}}
	cellsOut := report["cells"].(map[string]any)

	for _, cell := range cells {
		if cell.Role == "supervisor" {
			raw := runSupervisor(cell.Lane, cell.Profile)
			cellsOut[cell.ID] = applyContract(cell.ID, raw, exp)
			continue
		}
		okP, plugin, errP := buildPlugin(cell.Features, cell.Release)
		if !okP {
			cellsOut[cell.ID] = map[string]any{
				"status": "fail", "tls_model": "", "plugin_abi": "",
				"error": "plugin_build:" + errP,
			}
			continue
		}
		okH, host, buildDir, errH := buildHost(cell.Lane, cell.Profile)
		if !okH {
			cellsOut[cell.ID] = map[string]any{
				"status": "fail", "tls_model": "", "plugin_abi": "",
				"error": "host_build:" + errH,
			}
			continue
		}
		raw := runHost(host, plugin, buildDir)
		cellsOut[cell.ID] = applyContract(cell.ID, raw, exp)
	}

	_ = os.MkdirAll(filepath.Dir(outPath), 0o755)
	enc, _ := json.MarshalIndent(report, "", "  ")
	if err := os.WriteFile(outPath, append(enc, '\n'), 0o644); err != nil {
		fmt.Fprintf(os.Stderr, "write: %v\n", err)
		os.Exit(2)
	}
	fmt.Printf("wrote %s\n", outPath)
}

func safePath() string {
	if p := os.Getenv("LATTICE_SAFE_PATH"); p != "" {
		return p
	}
	return defaultSafePath
}

func resolveTool(name string) string {
	if name == "" || strings.Contains(name, string(os.PathSeparator)) {
		return name
	}
	for _, dir := range strings.Split(safePath(), ":") {
		if dir == "" {
			continue
		}
		cand := filepath.Join(dir, name)
		if st, err := os.Stat(cand); err == nil && !st.IsDir() {
			return cand
		}
	}
	return name
}

func withSafeEnv(extra []string) []string {
	base := os.Environ()
	if extra != nil {
		base = extra
	}
	out := make([]string, 0, len(base)+1)
	found := false
	sp := "PATH=" + safePath()
	for _, e := range base {
		if strings.HasPrefix(e, "PATH=") {
			out = append(out, sp)
			found = true
			continue
		}
		out = append(out, e)
	}
	if !found {
		out = append(out, sp)
	}
	return out
}

func run(cmd []string, dir string, env []string) (string, string, int) {
	if len(cmd) == 0 {
		return "", "", 1
	}
	argv := append([]string{}, cmd...)
	argv[0] = resolveTool(argv[0])
	c := exec.Command(argv[0], argv[1:]...)
	c.Dir = dir
	c.Env = withSafeEnv(env)
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

func parseCells(path string) ([]cellSpec, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var cells []cellSpec
	var cur *cellSpec
	flush := func() {
		if cur != nil {
			cells = append(cells, *cur)
			cur = nil
		}
	}
	for _, line := range strings.Split(string(raw), "\n") {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		if line == "[[cells]]" {
			flush()
			cur = &cellSpec{Lane: "musl", Profile: "target", Role: "host"}
			continue
		}
		if cur == nil || !strings.Contains(line, "=") {
			continue
		}
		parts := strings.SplitN(line, "=", 2)
		key := strings.TrimSpace(parts[0])
		val := strings.TrimSpace(parts[1])
		switch key {
		case "id":
			cur.ID = unquote(val)
		case "lane":
			cur.Lane = unquote(val)
		case "profile":
			cur.Profile = unquote(val)
		case "role":
			cur.Role = unquote(val)
		case "release":
			cur.Release = val == "true"
		case "features":
			inner := strings.Trim(val, "[]")
			var feats []string
			for _, x := range strings.Split(inner, ",") {
				x = strings.TrimSpace(x)
				x = unquote(x)
				if x != "" {
					feats = append(feats, x)
				}
			}
			cur.Features = feats
		}
	}
	flush()
	return cells, nil
}

func parseContract(path string) (map[string]map[string]string, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	out := map[string]map[string]string{}
	current := ""
	for _, line := range strings.Split(string(raw), "\n") {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		if strings.HasPrefix(line, "[cells.") && strings.HasSuffix(line, "]") {
			current = strings.TrimSuffix(strings.TrimPrefix(line, "[cells."), "]")
			out[current] = map[string]string{}
			continue
		}
		if current == "" || !strings.Contains(line, "=") {
			continue
		}
		parts := strings.SplitN(line, "=", 2)
		out[current][strings.TrimSpace(parts[0])] = unquote(strings.TrimSpace(parts[1]))
	}
	return out, nil
}

func unquote(s string) string {
	return strings.Trim(s, `"`)
}

func buildPlugin(features []string, release bool) (bool, string, string) {
	feat := "trunk"
	if len(features) > 0 {
		feat = strings.Join(features, ",")
	}
	cmd := []string{
		"cargo", "build", "-p", "p7",
		"--no-default-features", "--features", feat,
		"--manifest-path", filepath.Join(root, "Cargo.toml"),
	}
	if release {
		cmd = append(cmd, "--release")
	}
	out, _, rc := run(cmd, root, nil)
	if rc != 0 {
		return false, "", tail(out, 2000)
	}
	base := filepath.Join(root, "target", "debug")
	if release {
		base = filepath.Join(root, "target", "release")
	}
	for _, name := range []string{"libp7slot.so", "libp7slot.dylib"} {
		cand := filepath.Join(base, name)
		if _, err := os.Stat(cand); err == nil {
			return true, cand, ""
		}
	}
	deps := filepath.Join(base, "deps")
	matches, _ := filepath.Glob(filepath.Join(deps, "libp7slot*.so"))
	if len(matches) > 0 {
		return true, matches[len(matches)-1], ""
	}
	return false, "", "cdylib missing"
}

func buildHost(lane, profile string) (bool, string, string, string) {
	buildDir := filepath.Join(root, "build", fmt.Sprintf("h4-%s-%s", lane, profile))
	cmd := []string{
		"make", "-C", filepath.Join(root, "h4"),
		"ROOT=" + root,
		"BUILD=" + buildDir,
		"LANE=" + lane,
		"PROFILE=" + profile,
	}
	out, _, rc := run(cmd, root, nil)
	binary := filepath.Join(buildDir, "gateway_host")
	if rc != 0 {
		return false, "", buildDir, tail(out, 2000)
	}
	if _, err := os.Stat(binary); err != nil {
		return false, "", buildDir, tail(out, 2000)
	}
	return true, binary, buildDir, ""
}

func readHostFlags(buildDir string) map[string]string {
	path := filepath.Join(buildDir, "host.flags")
	out := map[string]string{}
	raw, err := os.ReadFile(path)
	if err != nil {
		return out
	}
	for _, line := range strings.Split(string(raw), "\n") {
		if !strings.Contains(line, "=") {
			continue
		}
		parts := strings.SplitN(line, "=", 2)
		out[strings.TrimSpace(parts[0])] = strings.TrimSpace(parts[1])
	}
	return out
}

func runHost(binary, plugin, buildDir string) map[string]any {
	out, _, rc := run([]string{binary, "--plugin", plugin}, root, nil)
	lines := nonEmptyLines(out)
	if len(lines) == 0 {
		return map[string]any{
			"status": "fail", "tls_model": "", "plugin_abi": "",
			"error": fmt.Sprintf("empty_host_output rc=%d", rc),
		}
	}
	var result map[string]any
	if err := json.Unmarshal([]byte(lines[len(lines)-1]), &result); err != nil {
		return map[string]any{
			"status": "fail", "tls_model": "", "plugin_abi": "",
			"error": "bad_json:" + trunc(lines[len(lines)-1], 200),
		}
	}
	flags := readHostFlags(buildDir)
	if len(flags) > 0 {
		result["flags"] = flags
	}
	return result
}

func runSupervisor(lane, profile string) map[string]any {
	env := append([]string{}, os.Environ()...)
	env = append(env, "XV_LANE="+lane, "XV_PROFILE="+profile)
	out, _, rc := run([]string{"go", "run", "."}, filepath.Join(root, "g3"), env)
	lines := nonEmptyLines(out)
	if len(lines) == 0 {
		return map[string]any{
			"status": "fail", "tls_model": "", "plugin_abi": "",
			"error": fmt.Sprintf("empty_supv rc=%d", rc),
		}
	}
	// Prefer the last JSON object line (ignore go build chatter).
	for i := len(lines) - 1; i >= 0; i-- {
		var result map[string]any
		if err := json.Unmarshal([]byte(lines[i]), &result); err == nil {
			return result
		}
	}
	return map[string]any{
		"status": "fail", "tls_model": "", "plugin_abi": "",
		"error": "bad_json:" + trunc(lines[len(lines)-1], 200),
	}
}

func applyContract(id string, result map[string]any, exp map[string]map[string]string) map[string]any {
	out := map[string]any{}
	for k, v := range result {
		out[k] = v
	}
	status, _ := out["status"].(string)
	if status != "ok" {
		return out
	}
	want := exp[id]
	if want == nil {
		return out
	}
	if tls, ok := want["tls_model"]; ok {
		if got, _ := out["tls_model"].(string); got != tls {
			out["status"] = "fail"
			out["error"] = "tls_model_mismatch"
		}
	}
	if abi, ok := want["plugin_abi"]; ok {
		if got, _ := out["plugin_abi"].(string); got != abi {
			out["status"] = "fail"
			out["error"] = "plugin_abi_mismatch"
		}
	}
	return out
}

func nonEmptyLines(s string) []string {
	var out []string
	for _, line := range strings.Split(s, "\n") {
		line = strings.TrimSpace(line)
		if line != "" {
			out = append(out, line)
		}
	}
	return out
}

func tail(s string, n int) string {
	if len(s) <= n {
		return s
	}
	return s[len(s)-n:]
}

func trunc(s string, n int) string {
	if len(s) <= n {
		return s
	}
	return s[:n]
}
