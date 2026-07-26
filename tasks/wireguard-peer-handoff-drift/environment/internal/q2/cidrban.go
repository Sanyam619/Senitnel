package q2

import (
    "sort"

    "wghandoff/internal/ingest"
)

// WantIDs returns the peer ids for epoch ep.
func WantIDs(b ingest.Bundle, ep int) []string {
    reserved := map[string]struct{}{}
    for _, row := range b.Table.Epochs {
        if row.Epoch >= ep {
            continue
        }
        for _, m := range row.Members {
            for _, cidr := range m.AllowedIPs {
                reserved[cidr] = struct{}{}
            }
        }
    }
    out := make([]string, 0)
    for _, m := range b.RowForEpoch(ep) {
        blocked := false
        for _, cidr := range m.AllowedIPs {
            if _, ok := reserved[cidr]; ok {
                blocked = true
                break
            }
        }
        if !blocked {
            out = append(out, m.ID)
        }
    }
    sort.Strings(out)
    return out
}
