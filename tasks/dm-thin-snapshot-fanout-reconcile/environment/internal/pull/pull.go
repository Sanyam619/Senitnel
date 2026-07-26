package pull

import (
	"fmt"
	"os"
	"path/filepath"

	"pool.lab/matfan/internal/fold"
	"pool.lab/matfan/internal/hold"
	"pool.lab/matfan/internal/skim"
	"pool.lab/matfan/internal/wire"
)

type Hit struct {
	Drill string
	Tip   string
	Kind  string
	Order int
	Bytes []byte
}

func Materialize(root, outDir, leaseDir string) ([]Hit, error) {
	rows, err := fold.RowsY(root)
	if err != nil {
		return nil, err
	}
	if err := os.MkdirAll(outDir, 0o755); err != nil {
		return nil, err
	}
	if err := os.MkdirAll(leaseDir, 0o755); err != nil {
		return nil, err
	}
	originRoot := os.Getenv("ORIGIN_ROOT")
	if originRoot == "" {
		originRoot = filepath.Join(root, "origins")
	}
	var hits []Hit
	for i, r := range rows {
		rel, err := hold.PhaseM(leaseDir, r.Tip)
		if err != nil {
			return nil, err
		}
		livePath := filepath.Join(originRoot, r.Origin+".bin")
		cowPath := filepath.Join(root, "snaps", "payloads", r.Tip+".bin")
		live, err := os.ReadFile(livePath)
		if err != nil {
			_ = rel()
			return nil, fmt.Errorf("origin %s: %w", livePath, err)
		}
		cow, err := os.ReadFile(cowPath)
		if err != nil {
			_ = rel()
			return nil, fmt.Errorf("snap %s: %w", cowPath, err)
		}
		live, err = skim.ShelfX(root, r.Drill, r.Origin, live)
		if err != nil {
			_ = rel()
			return nil, err
		}
		buf, kind, err := wire.SelectBuf(live, cow, r.Epoch, r.Floor)
		if err != nil {
			_ = rel()
			return nil, err
		}
		destDir := filepath.Join(outDir, r.Drill)
		if err := os.MkdirAll(destDir, 0o755); err != nil {
			_ = rel()
			return nil, err
		}
		dest := filepath.Join(destDir, "payload.bin")
		if err := os.WriteFile(dest, buf, 0o644); err != nil {
			_ = rel()
			return nil, err
		}
		if err := rel(); err != nil {
			return nil, err
		}
		hits = append(hits, Hit{
			Drill: r.Drill, Tip: r.Tip, Kind: kind, Order: i + 1, Bytes: buf,
		})
	}
	return hits, nil
}
