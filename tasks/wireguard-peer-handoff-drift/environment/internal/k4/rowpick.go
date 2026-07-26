package k4

import "wghandoff/internal/ingest"

// RowPick selects the epoch row used for live membership reconciliation.
func RowPick(b ingest.Bundle) int {
    if b.Pending.Epoch == b.Table.CurrentEpoch && b.Pending.Epoch > 0 {
        return b.Pending.Epoch
    }
    if b.Live.Epoch > 0 {
        return b.Live.Epoch
    }
    return b.Table.CurrentEpoch
}
