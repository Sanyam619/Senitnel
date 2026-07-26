package io

import (
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"csp.local/reconcile/internal/model"
)

func WriteAudit(path string, rows []model.AuditRow) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	sort.Slice(rows, func(i, j int) bool { return rows[i].LotID < rows[j].LotID })
	lines := []string{"lot_id\ttrays_blocked\ttrays_cleared\texposure_class"}
	for _, r := range rows {
		lines = append(lines, fmt.Sprintf("%s\t%d\t%d\t%s",
			r.LotID, r.TraysBlocked, r.TraysCleared, r.ExposureClass))
	}
	return os.WriteFile(path, []byte(strings.Join(lines, "\n")+"\n"), 0o644)
}
