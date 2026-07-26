package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"sort"

	"internal.example/matrixci/internal/graph"
	"internal.example/matrixci/internal/policy"
	"internal.example/matrixci/internal/resolve"
	"internal.example/matrixci/internal/vendorcheck"
)

var (
	proxyRoot  = flag.String("proxy", "/app/proxy", "module proxy root")
	repoRoot   = flag.String("repo", "/app/src", "monorepo root")
	policyPath = flag.String("policy", "/app/docs/security-pin-policy.md", "pin floor policy file")
	outPath    = flag.String("out", "", "write JSON report to path (default: stdout)")
)

type cellStatus struct {
	Status              string            `json:"status"`
	SelectedByMod       map[string]string `json:"selected"`
	VendorLedgerAgrees  bool              `json:"vendor_ledger_agrees"`
	Diagnostics         []string          `json:"diagnostics"`
}

type report struct {
	Toolchains              map[string]map[string]cellStatus `json:"toolchains"`
	CVEFloor                map[string]interface{}           `json:"cve_floor"`
	Retract                 map[string]interface{}           `json:"retract"`
	RequiredExcludes        map[string]interface{}           `json:"required_excludes"`
	ProhibitedReplaces      map[string]interface{}           `json:"prohibited_replaces"`
	RetainedForks           map[string]interface{}           `json:"retained_forks"`
	ReplaceConflicts        []string                         `json:"replace_conflicts"`
	VendorIncompatibleDrift []string                         `json:"vendor_incompatible_drift"`
	ProxyDigest             string                           `json:"proxy_digest"`
}

func main() {
	if len(os.Args) < 2 || os.Args[1] != "report" {
		fmt.Fprintln(os.Stderr, "usage: matrixci report [--out PATH]")
		os.Exit(2)
	}
	if err := flag.CommandLine.Parse(os.Args[2:]); err != nil {
		os.Exit(2)
	}

	proxyMods, proxyDigest, err := graph.LoadProxy(*proxyRoot)
	must(err)

	root, err := graph.LoadModFile(filepath.Join(*repoRoot, "go.mod"))
	must(err)
	sub, err := graph.LoadModFile(filepath.Join(*repoRoot, "svc", "go.mod"))
	must(err)

	constraints, err := policy.Load(*policyPath)
	must(err)

	toolsGuarded, err := graph.HasToolsBuildConstraint(filepath.Join(*repoRoot, "tools.go"))
	must(err)

	repConflicts := resolve.ReplaceConflicts(root, sub)
	if repConflicts == nil {
		repConflicts = []string{}
	}
	prohibitedHits := resolve.ProhibitedReplaceViolations(root, sub, constraints.ProhibitedReplaces)
	if prohibitedHits == nil {
		prohibitedHits = []string{}
	}
	retainedSpecs := make([]resolve.RetainedFork, 0, len(constraints.RetainedForks))
	for _, f := range constraints.RetainedForks {
		retainedSpecs = append(retainedSpecs, resolve.RetainedFork{
			Path:       f.Path,
			ForkPath:   f.ForkPath,
			MinVersion: f.MinVersion,
		})
	}
	retainedHits := resolve.RetainedForkViolations(root, sub, retainedSpecs)
	if retainedHits == nil {
		retainedHits = []string{}
	}
	// Policy required excludes are a root go.mod invariant; sub-tree
	// declarations do not satisfy them.
	rootDeclaredExcludes := resolve.DeclaredExcludes(root)
	required := make([]struct{ Path, Version string }, 0, len(constraints.RequiredExcludes))
	for _, e := range constraints.RequiredExcludes {
		required = append(required, struct{ Path, Version string }{e.Path, e.Version})
	}
	missingRequired := resolve.MissingRequiredExcludes(rootDeclaredExcludes, required)
	if missingRequired == nil {
		missingRequired = []string{}
	}

	r := report{
		Toolchains:              map[string]map[string]cellStatus{},
		CVEFloor:                map[string]interface{}{},
		Retract:                 map[string]interface{}{},
		RequiredExcludes:        map[string]interface{}{},
		ProhibitedReplaces:      map[string]interface{}{},
		RetainedForks:           map[string]interface{}{},
		ReplaceConflicts:        repConflicts,
		VendorIncompatibleDrift: []string{},
		ProxyDigest:             proxyDigest,
	}

	profiles := []string{"go1.22", "go1.23"}
	modes := []string{"mod", "vendor"}

	vendorMods, vendorDrift, err := vendorcheck.LoadModulesTxt(filepath.Join(*repoRoot, "bnd", "modules.txt"), proxyMods)
	must(err)
	if vendorDrift == nil {
		vendorDrift = []string{}
	}
	r.VendorIncompatibleDrift = vendorDrift

	// Compute the module resolution once per profile.
	selPerProfile := map[string]resolve.Selection{}
	for _, prof := range profiles {
		selPerProfile[prof] = resolve.SelectAll(root, sub, proxyMods, prof)
	}

	for _, prof := range profiles {
		cells := map[string]cellStatus{}
		sel := selPerProfile[prof]
		for _, mode := range modes {
			cell := cellStatus{
				SelectedByMod:      sel.SelectedVersions,
				VendorLedgerAgrees: true,
				Diagnostics:        []string{},
			}
			// Prohibited-replace diagnostics apply to every cell.
			if len(prohibitedHits) > 0 {
				cell.Status = firstNonEmpty(cell.Status, "prohibited-replace")
				cell.Diagnostics = append(cell.Diagnostics, prohibitedHits...)
			}
			// Missing required-exclude diagnostics apply to every cell.
			if len(missingRequired) > 0 {
				cell.Status = firstNonEmpty(cell.Status, "missing-required-exclude")
				cell.Diagnostics = append(cell.Diagnostics, missingRequired...)
			}
			// Dropping a policy-retained fork is a hard failure on every cell.
			if len(retainedHits) > 0 {
				cell.Status = firstNonEmpty(cell.Status, "retained-fork-missing")
				cell.Diagnostics = append(cell.Diagnostics, retainedHits...)
			}
			// Cross-tree replace disagreements fail every profile.
			if len(repConflicts) > 0 {
				cell.Status = firstNonEmpty(cell.Status, "replace-conflict")
				cell.Diagnostics = append(cell.Diagnostics, repConflicts...)
			}
			if sel.ToolchainTooOld {
				cell.Status = firstNonEmpty(cell.Status, "toolchain-too-old")
				cell.Diagnostics = append(cell.Diagnostics, sel.ToolchainReason)
			}
			if len(sel.ExcludedSelected) > 0 {
				cell.Status = firstNonEmpty(cell.Status, "excluded-selected")
				cell.Diagnostics = append(cell.Diagnostics, sel.ExcludedSelected...)
			}
			retractHits := resolve.RetractHits(sel.SelectedVersions, proxyMods)
			if len(retractHits) > 0 {
				cell.Status = firstNonEmpty(cell.Status, "retracted-selected")
				cell.Diagnostics = append(cell.Diagnostics, retractHits...)
			}
			floorHits := policy.FloorViolations(sel.SelectedVersions, constraints.Floors)
			if len(floorHits) > 0 {
				cell.Status = firstNonEmpty(cell.Status, "below-floor")
				cell.Diagnostics = append(cell.Diagnostics, floorHits...)
			}
			capHits := policy.CapViolations(sel.SelectedVersions, constraints.Caps)
			if len(capHits) > 0 {
				cell.Status = firstNonEmpty(cell.Status, "above-cap")
				cell.Diagnostics = append(cell.Diagnostics, capHits...)
			}
			// Vendor-specific checks.
			if mode == "vendor" {
				vh, vdiag := vendorcheck.VerifyAgainstSelection(sel.SelectedVersions, vendorMods, proxyMods)
				if !vh {
					cell.VendorLedgerAgrees = false
					cell.Status = firstNonEmpty(cell.Status, "vendor-drift")
					cell.Diagnostics = append(cell.Diagnostics, vdiag...)
				}
				if len(vendorDrift) > 0 {
					cell.VendorLedgerAgrees = false
					cell.Status = firstNonEmpty(cell.Status, "vendor-drift")
					cell.Diagnostics = append(cell.Diagnostics, vendorDrift...)
				}
				if !toolsGuarded {
					drags := resolve.ToolsDrag(root, proxyMods)
					if len(drags) > 0 {
						cell.Status = firstNonEmpty(cell.Status, "vendor-tool-drag")
						cell.Diagnostics = append(cell.Diagnostics, drags...)
					}
				}
			}
			if cell.Status == "" {
				cell.Status = "ok"
			}
			cell.Diagnostics = dedupe(cell.Diagnostics)
			sort.Strings(cell.Diagnostics)
			cells[mode] = cell
		}
		r.Toolchains[prof] = cells
	}

	// Top-level summaries use the go1.23 canonical resolution.
	canon := selPerProfile["go1.23"].SelectedVersions
	r.CVEFloor = policy.SummarizeFloor(canon, constraints)
	r.Retract = resolve.SummarizeRetracts(canon, proxyMods)
	r.RequiredExcludes = policy.SummarizeRequiredExcludes(constraints.RequiredExcludes, rootDeclaredExcludes)
	r.ProhibitedReplaces = policy.SummarizeProhibitedReplaces(prohibitedHits)
	r.RetainedForks = policy.SummarizeRetainedForks(constraints.RetainedForks, retainedHits)

	buf, err := json.MarshalIndent(r, "", "  ")
	must(err)
	buf = append(buf, '\n')

	if *outPath == "" {
		os.Stdout.Write(buf)
		return
	}
	must(os.MkdirAll(filepath.Dir(*outPath), 0o755))
	must(os.WriteFile(*outPath, buf, 0o644))
}

func firstNonEmpty(a, b string) string {
	if a != "" {
		return a
	}
	return b
}

func dedupe(in []string) []string {
	if len(in) == 0 {
		return in
	}
	seen := map[string]bool{}
	out := make([]string, 0, len(in))
	for _, s := range in {
		if seen[s] {
			continue
		}
		seen[s] = true
		out = append(out, s)
	}
	return out
}

func must(err error) {
	if err != nil {
		fmt.Fprintln(os.Stderr, "matrixci:", err)
		os.Exit(1)
	}
}
