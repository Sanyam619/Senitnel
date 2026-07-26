package guard

import "bgplab/internal/ingest"

func RevokeActive(r ingest.LoadedRoute, doc RoaDoc) bool {
    if len(doc.Entries) == 0 {
        return true
    }
    origin := routeOrigin(r.ASPath, r.PeerAS)
    var picked *RoaEntry
    for _, row := range doc.Entries {
        if !prefixExact(r.Prefix, row.Prefix) {
            continue
        }
        if row.OriginASN != origin {
            continue
        }
        if len(r.ASPath) >= row.MaxLength {
            continue
        }
        copy := row
        if picked == nil || copy.Serial < picked.Serial {
            picked = &copy
        }
    }
    return picked != nil && picked.State == "valid"
}
