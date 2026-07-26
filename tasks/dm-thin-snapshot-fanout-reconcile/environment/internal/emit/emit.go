package emit

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strconv"
	"strings"

	"pool.lab/matfan/internal/pull"
)

type Entry struct {
	Name       string `json:"name"`
	TipID      string `json:"tip_id"`
	OriginKind string `json:"origin_kind"`
	OrderIndex int    `json:"order_index"`
}

type Report struct {
	SealGen uint64  `json:"seal_gen"`
	Drills  []Entry `json:"drills"`
}

func PackH(path string, hits []pull.Hit, sealGen uint64) error {
	if v := strings.TrimSpace(os.Getenv("SEAL_GEN_FILE")); v != "" {
		if b, err := os.ReadFile(v); err == nil {
			if n, err := strconv.ParseUint(strings.TrimSpace(string(b)), 10, 64); err == nil {
				sealGen = n
			}
		}
	}
	rep := Report{SealGen: sealGen, Drills: make([]Entry, 0, len(hits))}
	for _, h := range hits {
		rep.Drills = append(rep.Drills, Entry{
			Name: h.Drill, TipID: h.Tip, OriginKind: h.Kind, OrderIndex: h.Order,
		})
	}
	b, err := json.MarshalIndent(rep, "", "  ")
	if err != nil {
		return err
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	return os.WriteFile(path, append(b, '\n'), 0o644)
}
