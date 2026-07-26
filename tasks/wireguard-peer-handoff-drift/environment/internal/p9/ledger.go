package p9

import "wghandoff/internal/ingest"

func LedgerEpoch(b ingest.Bundle) int {
    return b.Table.CurrentEpoch
}

func LiveEpoch(b ingest.Bundle) int {
    return b.Live.Epoch
}

func PendingEpoch(b ingest.Bundle) int {
    return b.Pending.Epoch
}
