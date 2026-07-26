package main

import (
	"encoding/json"
	"fmt"
	"math"
	"os"
	"path/filepath"
	"strconv"
	"strings"

	"nbody.campaign/runner/internal/buildmeta"
	"nbody.campaign/runner/internal/decoy"
	"nbody.campaign/runner/internal/partition"
	"nbody.campaign/runner/internal/policy"
	"nbody.campaign/runner/internal/reduce"
	"nbody.campaign/runner/internal/report"
	"nbody.campaign/runner/internal/snap"
	"nbody.campaign/runner/internal/tree"
)

const stride = 5

type caseCfg struct {
	N         int       `json:"n"`
	Steps     int       `json:"steps"`
	SnapAt    int       `json:"snap_at"`
	DT        float64   `json:"dt"`
	G         float64   `json:"G"`
	Kind      string    `json:"kind"`
	Particles []particle `json:"particles"`
}

type particle struct {
	X  float64 `json:"x"`
	Y  float64 `json:"y"`
	VX float64 `json:"vx"`
	VY float64 `json:"vy"`
	M  float64 `json:"m"`
}

type manCfg struct {
	U float64
	V float64
	P int
}

func parseManifest(path string) (manCfg, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return manCfg{}, err
	}
	var m manCfg
	m.U = 0.7
	m.V = 0.1
	m.P = 0
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
		case "theta":
			m.U, _ = strconv.ParseFloat(v, 64)
		case "soft":
			m.V, _ = strconv.ParseFloat(v, 64)
		case "fold_pref":
			if v == "tree" {
				m.P = 1
			} else {
				m.P = 0
			}
		}
	}
	return m, nil
}

func loadCase(path string) (caseCfg, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return caseCfg{}, err
	}
	var c caseCfg
	if err := json.Unmarshal(raw, &c); err != nil {
		return caseCfg{}, err
	}
	return c, nil
}

func allocState(cfg caseCfg, g int) []float64 {
	n := cfg.N
	if n == 0 {
		n = len(cfg.Particles)
	}
	state := partition.PadAlloc(n, g)
	src := make([]float64, n*stride)
	for i, p := range cfg.Particles {
		if i >= n {
			break
		}
		src[i*stride+0] = p.X
		src[i*stride+1] = p.Y
		src[i*stride+2] = p.VX
		src[i*stride+3] = p.VY
		src[i*stride+4] = p.M
	}
	partition.LoadInterior(state, src, n, g)
	partition.SortByX(state, n, g)
	partition.Exchange(state, n, g)
	return state
}

func runCase(label, root, mode string, workers int) (report.Row, error) {
	cfg, err := loadCase(filepath.Join(root, "data", "cases", label, "particles.json"))
	if err != nil {
		return report.Row{}, err
	}
	man, err := parseManifest(filepath.Join(root, "config", "manifests", label+".toml"))
	if err != nil {
		return report.Row{}, err
	}
	active := policy.Sel(
		policy.FromX(man.U, man.V, man.P),
		policy.FromY(buildmeta.U, buildmeta.V, buildmeta.P),
	)
	g := partition.HaloWidth()
	n := cfg.N
	if n == 0 {
		n = len(cfg.Particles)
	}
	state := allocState(cfg, g)
	ax := partition.Axis()

	start := 0
	snapPath := filepath.Join("/tmp", fmt.Sprintf("%s_w%d.snap", label, workers))
	if mode == "resume" {
		for t := 0; t < cfg.SnapAt; t++ {
			partition.Exchange(state, n, g)
			tree.Step(state, n, g, active.U, active.V, cfg.G, cfg.DT)
			partition.SortByX(state, n, g)
		}
		packed := snap.Encode(state, n, g, ax)
		if err := snap.WriteFile(snapPath, packed, n, cfg.SnapAt); err != nil {
			return report.Row{}, err
		}
		packed2, _, _, err := snap.ReadFile(snapPath)
		if err != nil {
			return report.Row{}, err
		}
		state = snap.Unpack(packed2, n, g)
		partition.Exchange(state, n, g)
		start = cfg.SnapAt
	}

	for t := start; t < cfg.Steps; t++ {
		if mode == "cold" && t == cfg.SnapAt {
			_ = snap.WriteFile(snapPath+".cold", snap.Encode(state, n, g, ax), n, t)
		}
		partition.Exchange(state, n, g)
		tree.Step(state, n, g, active.U, active.V, cfg.G, cfg.DT)
		partition.SortByX(state, n, g)
	}

	strips := partition.Split(n, workers)
	parts := make([]reduce.PartY, 0, len(strips))
	for _, s := range strips {
		view := partition.LocalView(state, s, n, g)
		parts = append(parts, reduce.PartY{
			State: view,
			I0:    s.I0,
			LN:    s.I1 - s.I0,
			G:     g,
		})
		_ = decoy.ProbeBounds(s.ID, s.I0, s.I1)
	}
	agg := reduce.Fold(parts, n, g)
	mass, momL2, ke := reduce.Macros(agg)
	pe := tree.PotentialEnergy(state, n, g, active.V, cfg.G)
	energy := ke + pe
	stable := !math.IsNaN(energy) && !math.IsInf(energy, 0) &&
		!math.IsNaN(momL2) && !math.IsNaN(mass) && mass > 0
	if active.P == 1 {
		_ = decoy.TracePartial(workers, mass)
	}
	return report.Row{
		Label:      label,
		Workers:    workers,
		Mode:       mode,
		Energy:     energy,
		MomentumL2: momL2,
		Mass:       mass,
		Stable:     stable,
	}, nil
}

func main() {
	root := "/app"
	if v := os.Getenv("NBODY_ROOT"); v != "" {
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
