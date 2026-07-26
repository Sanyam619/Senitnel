package kernel

import (
    "bgplab/internal/ingest"
    "bgplab/internal/policy"
)

func originRank(o string) int {
    switch o {
    case "igp":
        return 0
    case "egp":
        return 1
    case "incomplete":
        return 2
    default:
        return 3
    }
}

func neighborAS(r ingest.LoadedRoute) int {
    if len(r.ASPath) > 0 {
        return r.ASPath[0]
    }
    return r.PeerAS
}

func medComparable(a, b ingest.LoadedRoute, cfg policy.Config) bool {
    if cfg.AlwaysCompareMED {
        return true
    }
    return neighborAS(a) == neighborAS(b)
}

func shorterASPath(a, b []int) bool {
    if len(a) == len(b) {
        return false
    }
    return len(a) < len(b)
}

func Cmp_n4(a, b ingest.LoadedRoute, cfg policy.Config) bool {
    if a.LocalPref != b.LocalPref {
        return a.LocalPref > b.LocalPref
    }
    if shorterASPath(a.ASPath, b.ASPath) {
        return true
    }
    if len(a.ASPath) != len(b.ASPath) {
        return false
    }
    if originRank(a.Origin) != originRank(b.Origin) {
        return originRank(a.Origin) < originRank(b.Origin)
    }
    if medComparable(a, b, cfg) {
        if a.MED != b.MED {
            return a.MED < b.MED
        }
    }
    return a.PeerAddr < b.PeerAddr
}
