package main

import (
	"encoding/json"
	"fmt"
	"math"
	"os"
	"path/filepath"
	"strconv"
	"strings"

	"lbm.campaign/runner/internal/buildmeta"
	"lbm.campaign/runner/internal/decoy"
	"lbm.campaign/runner/internal/lattice"
	"lbm.campaign/runner/internal/partition"
	"lbm.campaign/runner/internal/policy"
	"lbm.campaign/runner/internal/reduce"
	"lbm.campaign/runner/internal/report"
	"lbm.campaign/runner/internal/snap"
)

type gridCfg struct {
	NX     int     `json:"nx"`
	NY     int     `json:"ny"`
	Rho0   float64 `json:"rho0"`
	Steps  int     `json:"steps"`
	SnapAt int     `json:"snap_at"`
	Fx     float64 `json:"fx"`
	Fy     float64 `json:"fy"`
	ULid   float64 `json:"u_lid"`
	Kind   string  `json:"kind"`
}

type manCfg struct {
	Omega float64
	Pref  int
}

func parseManifest(path string) (manCfg, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return manCfg{}, err
	}
	var m manCfg
	m.Omega = 1.0
	m.Pref = 0
	for _, line := range strings.Split(string(raw), "\n") {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		parts := strings.SplitN(line, "=", 2)
		if len(parts) != 2 {
			continue
		}
		k := strings.TrimSpace(parts[0])
		v := strings.Trim(strings.TrimSpace(parts[1]), `"`)
		switch k {
		case "omega":
			m.Omega, _ = strconv.ParseFloat(v, 64)
		case "fold_pref":
			if v == "tree" {
				m.Pref = 1
			} else {
				m.Pref = 0
			}
		}
	}
	return m, nil
}

func loadGrid(path string) (gridCfg, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return gridCfg{}, err
	}
	var g gridCfg
	if err := json.Unmarshal(raw, &g); err != nil {
		return gridCfg{}, err
	}
	return g, nil
}

func runCase(label, root, mode string, workers int) (report.Row, error) {
	g, err := loadGrid(filepath.Join(root, "data", "cases", label, "grid.json"))
	if err != nil {
		return report.Row{}, err
	}
	man, err := parseManifest(filepath.Join(root, "config", "manifests", label+".toml"))
	if err != nil {
		return report.Row{}, err
	}
	active := policy.Resolve(
		policy.FromManifest(man.Omega, man.Pref),
		policy.FromBuild(buildmeta.Omega, buildmeta.Pref),
	)
	const ghost = 1
	nx, ny := g.NX, g.NY
	f := lattice.Alloc(nx, ny, ghost)
	lattice.InitEquilibrium(f, nx, ny, ghost, g.Rho0, 0, 0)
	ax := partition.Axis()

	start := 0
	snapPath := filepath.Join("/tmp", fmt.Sprintf("%s_w%d.snap", label, workers))
	if mode == "resume" {
		// Produce a snapshot from a cold prefix, then reload via pack/unpack path.
		for t := 0; t < g.SnapAt; t++ {
			stepOnce(f, nx, ny, ghost, active.Omega, g)
		}
		packed := snap.Encode(f, nx, ny, ghost, ax)
		if err := snap.WriteFile(snapPath, packed, nx, ny, g.SnapAt); err != nil {
			return report.Row{}, err
		}
		packed2, _, _, _, err := snap.ReadFile(snapPath)
		if err != nil {
			return report.Row{}, err
		}
		f = snap.Unpack(packed2, nx, ny, ghost)
		start = g.SnapAt
	}

	for t := start; t < g.Steps; t++ {
		if mode == "cold" && t == g.SnapAt {
			// still take a snap on cold path for realism; do not reload
			_ = snap.WriteFile(snapPath+".cold", snap.Encode(f, nx, ny, ghost, ax), nx, ny, t)
		}
		stepOnce(f, nx, ny, ghost, active.Omega, g)
	}

	strips := partition.SplitX(nx, workers)
	parts := make([]reduce.PartY, 0, len(strips))
	for _, s := range strips {
		view := partition.LocalView(f, s, nx, ny, ghost)
		parts = append(parts, reduce.PartY{
			F:  view,
			X0: s.X0,
			LX: s.X1 - s.X0,
			NY: ny,
			G:  ghost,
		})
		_ = decoy.ProbeBounds(s.ID, s.X0, s.X1)
	}
	agg := reduce.Fold(parts, nx, ny, ghost)
	meanRho, momX, momY, ke, mass := reduce.Mean(agg)
	stable := !math.IsNaN(meanRho) && !math.IsInf(meanRho, 0) &&
		!math.IsNaN(momX) && !math.IsNaN(ke) && mass > 0
	// Prefer fold-based macros; fall back note via decoy when pref tree
	if active.Pref == 1 {
		_ = decoy.TracePartial(workers, mass)
	}
	return report.Row{
		Label:   label,
		Workers: workers,
		Mode:    mode,
		MeanRho: meanRho,
		MomX:    momX,
		MomY:    momY,
		KE:      ke,
		Mass:    mass,
		Stable:  stable,
	}, nil
}

func stepOnce(f []float64, nx, ny, g int, omega float64, cfg gridCfg) {
	partition.ExchangeX(f, nx, ny, g)
	partition.ExchangeY(f, nx, ny, g)
	lattice.Collide(f, nx, ny, g, omega, cfg.Fx, cfg.Fy)
	lattice.Stream(f, nx, ny, g)
	if cfg.Kind == "cavity" || cfg.Kind == "couette" {
		lattice.ApplyLid(f, nx, ny, g, cfg.ULid)
	}
}

func main() {
	root := "/app"
	if v := os.Getenv("LBM_ROOT"); v != "" {
		root = v
	}
	outPath := "/output/campaign-report.json"
	if len(os.Args) > 1 {
		outPath = os.Args[1]
	}
	labels, err := decoy.ScanManifests(filepath.Join(root, "config", "manifests"))
	if err != nil {
		fmt.Fprintf(os.Stderr, "scan: %v\n", err)
		os.Exit(1)
	}
	workersList := []int{1, 2, 4}
	modes := []string{"cold", "resume"}
	var rows []report.Row
	for _, label := range labels {
		for _, w := range workersList {
			for _, mode := range modes {
				row, err := runCase(label, root, mode, w)
				if err != nil {
					fmt.Fprintf(os.Stderr, "case %s: %v\n", label, err)
					os.Exit(1)
				}
				rows = append(rows, row)
			}
		}
	}
	if err := report.Write(outPath, rows); err != nil {
		fmt.Fprintf(os.Stderr, "write: %v\n", err)
		os.Exit(1)
	}
	fmt.Printf("wrote %s (%d rows)\n", outPath, len(rows))
}
