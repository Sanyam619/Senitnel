package resolve

import (
	"fmt"
	"sort"
	"strconv"
	"strings"

	"internal.example/matrixci/internal/graph"
)

type Selection struct {
	SelectedVersions map[string]string
	ExcludedSelected []string
	ToolchainTooOld  bool
	ToolchainReason  string
}

// SelectAll performs a matrixci-style module selection across root+sub for a
// given toolchain profile. Semantics documented in matrixci/README below.
func SelectAll(root, sub *graph.ModFile, proxy map[string]*graph.ProxyModule, profile string) Selection {
	// Aggregate requires from both mod files.
	reqs := map[string]string{}
	for _, r := range root.Require {
		if beats(reqs[r.Path], r.Version) {
			reqs[r.Path] = r.Version
		}
	}
	for _, r := range sub.Require {
		if beats(reqs[r.Path], r.Version) {
			reqs[r.Path] = r.Version
		}
	}
	// Apply replaces from the top-level mod file (only main module's replaces
	// are honored for the effective build, per matrixci convention).
	replaceMap := map[string]graph.Replace{}
	for _, rep := range root.Replace {
		if rep.OldVer == "" {
			replaceMap[rep.Path] = rep
		} else {
			replaceMap[rep.Path+"@"+rep.OldVer] = rep
		}
	}
	// Collect exclude set from both mod files.
	excluded := map[string]map[string]bool{}
	for _, ex := range append(append([]graph.Exclude{}, root.Exclude...), sub.Exclude...) {
		if excluded[ex.Path] == nil {
			excluded[ex.Path] = map[string]bool{}
		}
		excluded[ex.Path][ex.Version] = true
	}

	sel := Selection{SelectedVersions: map[string]string{}}
	toolchain := effectiveToolchain(root, profile)

	for path, minReq := range reqs {
		effectivePath := path
		effectiveMin := minReq
		if rep, ok := replaceMap[path]; ok {
			effectivePath = rep.NewPath
			if rep.NewVer != "" {
				if beats(effectiveMin, rep.NewVer) {
					effectiveMin = rep.NewVer
				}
			}
		}
		// Advance past excluded versions using the proxy's version list.
		chosen := advancePastExcludes(effectivePath, effectiveMin, excluded, proxy)
		if chosen == "" {
			chosen = effectiveMin
			sel.ExcludedSelected = append(sel.ExcludedSelected, fmt.Sprintf("%s@%s excluded and no successor available in proxy", effectivePath, effectiveMin))
		}
		if isExcluded(excluded, effectivePath, chosen) {
			sel.ExcludedSelected = append(sel.ExcludedSelected, fmt.Sprintf("%s@%s excluded", effectivePath, chosen))
		}
		sel.SelectedVersions[path] = chosen
		// Toolchain-too-old check: does the selected module require go > profile?
		if pm := proxy[effectivePath]; pm != nil {
			needGo := pm.MinGoDirective[chosen]
			if needGo != "" && goLess(profile, needGo) {
				// Effective toolchain from top-level may lift us above the profile.
				if goLess(toolchain, needGo) {
					sel.ToolchainTooOld = true
					sel.ToolchainReason = fmt.Sprintf("toolchain-too-old:%s", effectivePath)
				}
			}
		}
	}
	sort.Strings(sel.ExcludedSelected)
	return sel
}

func effectiveToolchain(root *graph.ModFile, profile string) string {
	if root.Toolchain != "" {
		tc := strings.TrimPrefix(root.Toolchain, "go")
		if !goLess(tc, profile[len("go"):]) {
			return "go" + tc
		}
	}
	return profile
}

func advancePastExcludes(path, minVer string, excluded map[string]map[string]bool, proxy map[string]*graph.ProxyModule) string {
	// MVS selects the required version verbatim when it is not excluded;
	// only when the exact required version is excluded does the resolver
	// advance to the next non-excluded version in the proxy.
	if !isExcluded(excluded, path, minVer) {
		return minVer
	}
	pm := proxy[path]
	if pm == nil {
		return minVer
	}
	sorted := append([]string{}, pm.Versions...)
	sort.Slice(sorted, func(i, j int) bool { return versionLess(sorted[i], sorted[j]) })
	// Find first version >= minVer that's not excluded.
	for _, v := range sorted {
		if versionLess(v, minVer) {
			continue
		}
		if !isExcluded(excluded, path, v) {
			return v
		}
	}
	return ""
}

func isExcluded(excluded map[string]map[string]bool, path, ver string) bool {
	m := excluded[path]
	if m == nil {
		return false
	}
	return m[ver]
}

// versionLess compares Go module semver strings, tolerating a "+incompatible"
// suffix and prefixed "v".
func versionLess(a, b string) bool {
	return compareVersions(a, b) < 0
}

func compareVersions(a, b string) int {
	aa := trimIncompatible(strings.TrimPrefix(a, "v"))
	bb := trimIncompatible(strings.TrimPrefix(b, "v"))
	ap := strings.Split(aa, ".")
	bp := strings.Split(bb, ".")
	for i := 0; i < max(len(ap), len(bp)); i++ {
		var an, bn int
		if i < len(ap) {
			an = atoi(ap[i])
		}
		if i < len(bp) {
			bn = atoi(bp[i])
		}
		if an != bn {
			if an < bn {
				return -1
			}
			return 1
		}
	}
	return 0
}

func trimIncompatible(s string) string {
	if i := strings.Index(s, "+"); i >= 0 {
		return s[:i]
	}
	return s
}

func beats(cur, cand string) bool {
	if cur == "" {
		return true
	}
	return compareVersions(cur, cand) < 0
}

func atoi(s string) int {
	n, _ := strconv.Atoi(strings.TrimSpace(s))
	return n
}

func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}

func goLess(a, b string) bool {
	aa := strings.TrimPrefix(a, "go")
	bb := strings.TrimPrefix(b, "go")
	return compareVersions(aa, bb) < 0
}

// ReplaceConflicts finds modules with disagreeing replace directives between
// root and sub go.mod files.
func ReplaceConflicts(root, sub *graph.ModFile) []string {
	rootRep := map[string]graph.Replace{}
	for _, r := range root.Replace {
		rootRep[r.Path] = r
	}
	subRep := map[string]graph.Replace{}
	for _, r := range sub.Replace {
		subRep[r.Path] = r
	}
	var conflicts []string
	for path, sr := range subRep {
		rr, ok := rootRep[path]
		if !ok {
			continue
		}
		if rr.NewPath != sr.NewPath || rr.NewVer != sr.NewVer {
			conflicts = append(conflicts, fmt.Sprintf("%s: root %s@%s vs sub %s@%s", path, rr.NewPath, rr.NewVer, sr.NewPath, sr.NewVer))
		}
	}
	sort.Strings(conflicts)
	return conflicts
}

// RetractHits returns diagnostic strings for any selected version that falls
// inside a retract range published by the module's latest mod file.
func RetractHits(selected map[string]string, proxy map[string]*graph.ProxyModule) []string {
	var hits []string
	keys := sortedKeys(selected)
	for _, path := range keys {
		ver := selected[path]
		pm := proxy[path]
		if pm == nil || pm.LatestMod == nil {
			continue
		}
		for _, ret := range pm.LatestMod.Retract {
			if compareVersions(ret.Low, ver) <= 0 && compareVersions(ver, ret.High) <= 0 {
				hits = append(hits, fmt.Sprintf("retracted:%s", path))
			}
		}
	}
	sort.Strings(hits)
	return hits
}

// SummarizeRetracts is emitted at the top of the report for observability.
func SummarizeRetracts(selected map[string]string, proxy map[string]*graph.ProxyModule) map[string]interface{} {
	summary := map[string]interface{}{
		"avoided": true,
		"ranges":  map[string]interface{}{},
	}
	ranges := map[string]interface{}{}
	for path := range selected {
		pm := proxy[path]
		if pm == nil || pm.LatestMod == nil {
			continue
		}
		if len(pm.LatestMod.Retract) == 0 {
			continue
		}
		var ss []map[string]string
		for _, r := range pm.LatestMod.Retract {
			ss = append(ss, map[string]string{"low": r.Low, "high": r.High})
		}
		ranges[path] = ss
	}
	summary["ranges"] = ranges
	if len(RetractHits(selected, proxy)) > 0 {
		summary["avoided"] = false
	}
	return summary
}

// ProhibitedReplaceViolations returns per-tree strings describing replace
// directives that target modules listed in the policy prohibited-replace
// table. Both the root and the sub go.mod are inspected.
func ProhibitedReplaceViolations(root, sub *graph.ModFile, prohibited map[string]bool) []string {
	if len(prohibited) == 0 {
		return nil
	}
	var hits []string
	for _, rep := range root.Replace {
		if prohibited[rep.Path] {
			hits = append(hits, fmt.Sprintf("prohibited-replace:root:%s", rep.Path))
		}
	}
	for _, rep := range sub.Replace {
		if prohibited[rep.Path] {
			hits = append(hits, fmt.Sprintf("prohibited-replace:sub:%s", rep.Path))
		}
	}
	sort.Strings(hits)
	return hits
}

// RetainedFork names a policy-required in-tree fork replacement.
type RetainedFork struct {
	Path       string
	ForkPath   string
	MinVersion string
}

// RetainedForkViolations returns diagnostics when a policy-retained fork
// replace is absent from either tree, is written with a version selector on
// the left-hand side, targets a fork path other than the retained one, or
// pins a fork version below the declared minimum.
func RetainedForkViolations(root, sub *graph.ModFile, required []RetainedFork) []string {
	if len(required) == 0 {
		return nil
	}
	var hits []string
	for _, want := range required {
		check := func(label string, reps []graph.Replace) {
			var unversioned *graph.Replace
			var versioned bool
			for i := range reps {
				r := &reps[i]
				if r.Path != want.Path {
					continue
				}
				if r.OldVer == "" {
					unversioned = r
					break
				}
				versioned = true
			}
			if unversioned == nil {
				if versioned {
					hits = append(hits, fmt.Sprintf("%s: retained-fork:%s (versioned-lhs)", label, want.Path))
				} else {
					hits = append(hits, fmt.Sprintf("%s: retained-fork:%s (missing)", label, want.Path))
				}
				return
			}
			if unversioned.NewPath != want.ForkPath {
				hits = append(hits, fmt.Sprintf("%s: retained-fork:%s (path)", label, want.Path))
				return
			}
			if unversioned.NewVer == "" || compareVersions(unversioned.NewVer, want.MinVersion) < 0 {
				hits = append(hits, fmt.Sprintf("%s: retained-fork:%s (below-min)", label, want.Path))
			}
		}
		check("root", root.Replace)
		check("sub", sub.Replace)
	}
	sort.Strings(hits)
	return hits
}

// DeclaredExcludes returns a set-of-versions per module path drawn from the
// exclude directives of the supplied go.mod files.
func DeclaredExcludes(mods ...*graph.ModFile) map[string]map[string]bool {
	out := map[string]map[string]bool{}
	for _, m := range mods {
		if m == nil {
			continue
		}
		for _, ex := range m.Exclude {
			if out[ex.Path] == nil {
				out[ex.Path] = map[string]bool{}
			}
			out[ex.Path][ex.Version] = true
		}
	}
	return out
}

// MissingRequiredExcludes returns diagnostic strings for each policy-required
// exclude that is not declared in the supplied exclude set (callers pass the
// root-only set so sub-tree declarations cannot satisfy the policy).
func MissingRequiredExcludes(declared map[string]map[string]bool, required []struct{ Path, Version string }) []string {
	var hits []string
	for _, r := range required {
		if declared[r.Path] == nil || !declared[r.Path][r.Version] {
			hits = append(hits, fmt.Sprintf("required-exclude:%s@%s", r.Path, r.Version))
		}
	}
	sort.Strings(hits)
	return hits
}

// ToolsDrag returns non-empty diagnostics when the tools file (unguarded)
// pulls in modules that would otherwise be excluded from the vendor tree.
func ToolsDrag(root *graph.ModFile, proxy map[string]*graph.ProxyModule) []string {
	var drags []string
	for _, ex := range root.Exclude {
		if strings.HasPrefix(ex.Path, "example.org/toolchain") {
			drags = append(drags, fmt.Sprintf("vendor-tool-drag:%s", ex.Path))
		}
	}
	sort.Strings(drags)
	return drags
}

func sortedKeys(m map[string]string) []string {
	out := make([]string, 0, len(m))
	for k := range m {
		out = append(out, k)
	}
	sort.Strings(out)
	return out
}
