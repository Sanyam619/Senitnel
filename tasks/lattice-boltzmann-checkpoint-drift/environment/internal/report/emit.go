package report

import (
	"encoding/json"
	"math"
	"os"
	"path/filepath"
)

// Row is one campaign measurement.
type Row struct {
	Label   string  `json:"label"`
	Workers int     `json:"workers"`
	Mode    string  `json:"mode"`
	MeanRho float64 `json:"mean_rho"`
	MomX    float64 `json:"mom_x"`
	MomY    float64 `json:"mom_y"`
	KE      float64 `json:"ke"`
	Mass    float64 `json:"mass"`
	Stable  bool    `json:"stable"`
}

// Parity holds cross-mode relative gaps.
type Parity struct {
	ColdResumeMaxRel  float64 `json:"cold_resume_max_rel"`
	WorkerSpreadMaxRel float64 `json:"worker_spread_max_rel"`
}

// Doc is the top-level report.
type Doc struct {
	SchemaTag string `json:"schema_tag"`
	Cases     []Row  `json:"cases"`
	Parity    Parity `json:"parity"`
}

const SchemaTag = "lbm-campaign-v1"

func relGap(a, b float64) float64 {
	den := math.Max(math.Max(math.Abs(a), math.Abs(b)), 1e-12)
	return math.Abs(a-b) / den
}

func relSpread(vals []float64) float64 {
	if len(vals) == 0 {
		return 0
	}
	lo, hi := vals[0], vals[0]
	for _, v := range vals[1:] {
		if v < lo {
			lo = v
		}
		if v > hi {
			hi = v
		}
	}
	den := math.Max(math.Max(math.Abs(lo), math.Abs(hi)), 1e-12)
	return (hi - lo) / den
}

// ComputeParity fills parity from rows.
func ComputeParity(rows []Row) Parity {
	var p Parity
	type key struct {
		label string
		w     int
	}
	by := map[key]map[string]Row{}
	for _, r := range rows {
		k := key{r.Label, r.Workers}
		if by[k] == nil {
			by[k] = map[string]Row{}
		}
		by[k][r.Mode] = r
	}
	for _, modes := range by {
		c, okc := modes["cold"]
		r, okr := modes["resume"]
		if !okc || !okr {
			continue
		}
		for _, g := range []float64{
			relGap(c.MeanRho, r.MeanRho),
			relGap(c.MomX, r.MomX),
			relGap(c.MomY, r.MomY),
			relGap(c.KE, r.KE),
			relGap(c.Mass, r.Mass),
		} {
			if g > p.ColdResumeMaxRel {
				p.ColdResumeMaxRel = g
			}
		}
	}
	labels := map[string][]Row{}
	for _, r := range rows {
		if r.Mode != "cold" {
			continue
		}
		labels[r.Label] = append(labels[r.Label], r)
	}
	for _, group := range labels {
		fields := []func(Row) float64{
			func(r Row) float64 { return r.MeanRho },
			func(r Row) float64 { return r.MomX },
			func(r Row) float64 { return r.MomY },
			func(r Row) float64 { return r.KE },
			func(r Row) float64 { return r.Mass },
		}
		for _, get := range fields {
			vals := make([]float64, len(group))
			for i, r := range group {
				vals[i] = get(r)
			}
			s := relSpread(vals)
			if s > p.WorkerSpreadMaxRel {
				p.WorkerSpreadMaxRel = s
			}
		}
	}
	return p
}

// Write emits the report JSON.
func Write(path string, rows []Row) error {
	doc := Doc{
		SchemaTag: SchemaTag,
		Cases:     rows,
		Parity:    ComputeParity(rows),
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	raw, err := json.MarshalIndent(doc, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, raw, 0o644)
}
