package m7

import "wghandoff/internal/ingest"

// Absent_ok reports whether superseded peers from earlier rotations are gone.
func Absent_ok(b ingest.Bundle) bool {
    live := map[string]struct{}{}
    for _, id := range b.Live.MemberIDs {
        live[id] = struct{}{}
    }
    for _, row := range b.Table.Epochs {
        if row.Epoch >= b.Manifest.TargetEpoch {
            continue
        }
        for _, m := range row.Members {
            if _, ok := live[m.ID]; ok {
                return false
            }
        }
    }
    return true
}

func Drift_count(b ingest.Bundle, want []string) int {
    live := map[string]struct{}{}
    for _, id := range b.Live.MemberIDs {
        live[id] = struct{}{}
    }
    wantSet := map[string]struct{}{}
    for _, id := range want {
        wantSet[id] = struct{}{}
    }
    drift := 0
    for id := range live {
        if _, ok := wantSet[id]; !ok {
            drift++
        }
    }
    return drift
}
