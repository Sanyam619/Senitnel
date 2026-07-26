package ormanifest

import (
	"path/filepath"
	"strconv"

	csv "csp.local/reconcile/internal/io"
)

func Load(dir string) ([]Row, error) {
	rows, err := csv.ReadCSV(filepath.Join(dir, "or_manifest.csv"))
	if err != nil {
		return nil, err
	}
	var out []Row
	for _, c := range rows {
		cs, _ := strconv.Atoi(c[3])
		out = append(out, Row{CaseID: c[0], TrayID: c[1], RoomID: c[2], CaseStartEpoch: cs})
	}
	return out, nil
}
