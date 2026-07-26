package fold

import (
	"fmt"
	"os"
	"path/filepath"
	"sort"

	"pool.lab/matfan/internal/catalog"
)

func PhaseK(root string, capGen uint64) error {
	return phase_k(root, capGen)
}

func phase_k(root string, capGen uint64) error {
	wal := filepath.Join(root, "journal", "act.wal")
	rows, err := ingest_x(wal)
	if err != nil {
		return err
	}
	rosterPath := getenv("DRILL_ROSTER", "/etc/pool/drill.roster")
	names, err := catalog.RosterNames(rosterPath)
	if err != nil {
		return err
	}
	allow := map[string]bool{}
	for _, n := range names {
		allow[n] = true
	}
	filtered := make([]Row, 0, len(rows))
	for _, r := range rows {
		if r.Gen > capGen {
			continue
		}
		if !allow[r.Drill] {
			continue
		}
		filtered = append(filtered, r)
	}
	sort.Slice(filtered, func(i, j int) bool {
		if filtered[i].Gen != filtered[j].Gen {
			return filtered[i].Gen < filtered[j].Gen
		}
		return filtered[i].Seq < filtered[j].Seq
	})
	latest := map[string]Row{}
	var orderKeys []string
	seen := map[string]bool{}
	for _, r := range filtered {
		if !seen[r.Drill] {
			orderKeys = append(orderKeys, r.Drill)
			seen[r.Drill] = true
		}
		latest[r.Drill] = r
	}
	runtime := filepath.Join(root, "meta", "runtime.tsv")
	f, err := os.Create(runtime)
	if err != nil {
		return err
	}
	defer f.Close()
	for i, drill := range orderKeys {
		r := latest[drill]
		line := fmt.Sprintf("%d\t%s\t%s\t%s\t%s\t%d\t%d\n",
			i+1, r.Drill, r.Tip, r.Origin, r.Kind, r.Epoch, r.Floor)
		if _, err := f.WriteString(line); err != nil {
			return err
		}
	}
	return ScrubW(root)
}

func getenv(k, def string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return def
}
