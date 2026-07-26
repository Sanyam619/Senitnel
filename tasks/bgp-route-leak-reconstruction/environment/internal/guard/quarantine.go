package guard

import "bgplab/internal/ingest"

func Held(r ingest.LoadedRoute, doc QuarantineDoc) bool {
    for _, row := range doc.Holds {
        if row.Prefix != r.Prefix || row.Peer != r.Peer {
            continue
        }
        if row.Reason != "export_hold" {
            continue
        }
        return true
    }
    return false
}
