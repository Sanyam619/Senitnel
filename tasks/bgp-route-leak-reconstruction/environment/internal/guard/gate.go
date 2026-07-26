package guard

import (
    "bgplab/internal/ingest"
    "bgplab/internal/kernel"
    "bgplab/internal/policy"
)

func Admit(r ingest.LoadedRoute, cfg policy.Config, tab Tables) bool {
    if !kernel.Ok_m2(r.ASPath, cfg.LocalAS) {
        return false
    }
    if Held(r, tab.Quarantine) {
        return false
    }
    if !MatchRoa(r, tab.Roa) {
        return false
    }
    return RevokeActive(r, tab.Roa)
}
