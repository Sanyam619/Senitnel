package r6

import "wghandoff/internal/ingest"

// QueueIDs mirrors the pending queue for audit tooling.
func QueueIDs(b ingest.Bundle) []string {
    return append([]string(nil), b.Pending.MemberIDs...)
}

func QueueEpoch(b ingest.Bundle) int {
    return b.Pending.Epoch
}
