package lotnotice

import (
	"path/filepath"
	"strconv"

	csv "csp.local/reconcile/internal/io"
)

func Load(dir string) ([]Row, error) {
	rows, err := csv.ReadCSV(filepath.Join(dir, "lot_notice.csv"))
	if err != nil {
		return nil, err
	}
	var out []Row
	for _, c := range rows {
		eff, _ := strconv.Atoi(c[2])
		out = append(out, Row{LotID: c[0], ZoneID: c[1], EffectiveTS: eff, RecallClass: c[3]})
	}
	return out, nil
}
