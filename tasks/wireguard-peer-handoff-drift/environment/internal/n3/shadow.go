package n3

import "wghandoff/internal/ingest"

// ShadowPick mirrors row selection for the decoy audit path.
func ShadowPick(b ingest.Bundle) int {
    if b.Live.Epoch > 0 {
        return b.Live.Epoch
    }
    return b.Table.CurrentEpoch
}

func ShadowIDs(b ingest.Bundle, ep int) []string {
    return ingest.MemberIDs(b.RowForEpoch(ep))
}
