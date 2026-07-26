package guard

import "bgplab/internal/ingest"

func routeOrigin(path []int, peerAS int) int {
    if len(path) == 0 {
        return peerAS
    }
    return path[0]
}

func prefixExact(routePrefix, roaPrefix string) bool {
    return routePrefix == roaPrefix
}

func MatchRoa(r ingest.LoadedRoute, doc RoaDoc) bool {
    if len(doc.Entries) == 0 {
        return true
    }
    origin := routeOrigin(r.ASPath, r.PeerAS)
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
        if row.State != "valid" {
            continue
        }
        return true
    }
    return false
}
