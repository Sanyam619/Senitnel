package scanfeed

import (
	"path/filepath"
	"strconv"

	csv "csp.local/reconcile/internal/io"
)

func Load(dir string) ([]Row, error) {
	rows, err := csv.ReadCSV(filepath.Join(dir, "scan_feed.csv"))
	if err != nil {
		return nil, err
	}
	var out []Row
	for _, c := range rows {
		ts, _ := strconv.Atoi(c[1])
		out = append(out, Row{TrayID: c[0], TSEpoch: ts, ZoneID: c[2], EventCode: c[3]})
	}
	return out, nil
}
