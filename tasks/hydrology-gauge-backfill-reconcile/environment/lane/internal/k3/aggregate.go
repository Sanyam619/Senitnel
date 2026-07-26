package k3

import (
	"encoding/json"
	"os"
	"path/filepath"

	"lab.local/hydro_lane/pkg/frame"
)

func MergedAggregate(dataRoot, channel string, ts int64) (int, int64, error) {
	path := filepath.Join(dataRoot, "columns", channel+"_merged.col")
	raw, err := os.ReadFile(path)
	if err != nil {
		return 0, 0, err
	}
	var stripe frame.ColumnStripe
	if err := json.Unmarshal(raw, &stripe); err != nil {
		return 0, 0, err
	}
	count := 0
	var sum int64
	for _, rec := range stripe.Records {
		if rec.T <= ts {
			count++
			sum += rec.T
		}
	}
	return count, sum, nil
}
