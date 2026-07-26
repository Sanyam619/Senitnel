package kernel

import (
    "sort"

    "bgplab/internal/ingest"
    "bgplab/internal/policy"
)

func Pick_r7(routes []ingest.LoadedRoute, cfg policy.Config) *ingest.LoadedRoute {
    usable := make([]ingest.LoadedRoute, 0, len(routes))
    for _, r := range routes {
        if Ok_m2(r.ASPath, cfg.LocalAS) {
            usable = append(usable, r)
        }
    }
    sort.Slice(usable, func(i, j int) bool {
        if usable[i].Prefix != usable[j].Prefix {
            return usable[i].Prefix < usable[j].Prefix
        }
        return usable[i].Peer < usable[j].Peer
    })
    var best *ingest.LoadedRoute
    for i := range usable {
        r := &usable[i]
        if best == nil || Cmp_n4(*r, *best, cfg) {
            best = r
        }
    }
    return best
}
