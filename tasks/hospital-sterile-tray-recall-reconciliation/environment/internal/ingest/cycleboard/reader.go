package cycleboard

import (
	"path/filepath"
	"strconv"

	csv "csp.local/reconcile/internal/io"
)

func Load(dir string) ([]Row, error) {
	rows, err := csv.ReadCSV(filepath.Join(dir, "cycle_board.csv"))
	if err != nil {
		return nil, err
	}
	var out []Row
	for _, c := range rows {
		cs, _ := strconv.Atoi(c[2])
		ce, _ := strconv.Atoi(c[3])
		out = append(out, Row{LoadID: c[0], ZoneID: c[1], CycleStart: cs, CycleEnd: ce, Chamber: c[4]})
	}
	return out, nil
}
