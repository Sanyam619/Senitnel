package setcatalog

import (
	"path/filepath"

	csv "csp.local/reconcile/internal/io"
)

func Load(dir string) ([]Row, error) {
	rows, err := csv.ReadCSV(filepath.Join(dir, "set_catalog.csv"))
	if err != nil {
		return nil, err
	}
	var out []Row
	for _, c := range rows {
		if len(c) < 2 || c[0] == "" {
			continue
		}
		out = append(out, Row{ParentTray: c[0], ChildTray: c[1]})
	}
	return out, nil
}
