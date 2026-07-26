package report

import (
    "encoding/json"
    "os"
    "sort"

    "bgplab/internal/guard"
    "bgplab/internal/ingest"
    "bgplab/internal/kernel"
    "bgplab/internal/policy"
)

type FibEntry struct {
    Prefix   string `json:"prefix"`
    Peer     string `json:"peer"`
    NextHop  string `json:"next_hop"`
    ASPath   []int  `json:"as_path"`
}

type LeakItem struct {
    Prefix  string `json:"prefix"`
    Peer    string `json:"peer"`
    ASPath  []int  `json:"as_path"`
}

type FibDoc map[string][]FibEntry
type LeakDoc struct {
    Items []LeakItem `json:"items"`
}

func stockHeld(r ingest.LoadedRoute, doc guard.QuarantineDoc) bool {
    for _, row := range doc.Holds {
        if row.Peer == r.Peer {
            return true
        }
    }
    return false
}

func stockRoa(r ingest.LoadedRoute, doc guard.RoaDoc) bool {
    for _, row := range doc.Entries {
        if row.Prefix == r.Prefix {
            return true
        }
    }
    return len(doc.Entries) == 0
}

func stockAdmit(r ingest.LoadedRoute, cfg policy.Config, tab guard.Tables) bool {
    if !kernel.Ok_m2(r.ASPath, cfg.LocalAS) {
        return false
    }
    if stockHeld(r, tab.Quarantine) {
        return false
    }
    return stockRoa(r, tab.Roa)
}

func filterAdmit(routes []ingest.LoadedRoute, cfg policy.Config, tab guard.Tables, admit func(ingest.LoadedRoute, policy.Config, guard.Tables) bool) []ingest.LoadedRoute {
    out := make([]ingest.LoadedRoute, 0, len(routes))
    for _, r := range routes {
        if admit(r, cfg, tab) {
            out = append(out, r)
        }
    }
    return out
}

func routesDiffer(a, b *ingest.LoadedRoute) bool {
    if a == nil || b == nil {
        return a != b
    }
    if a.Peer != b.Peer {
        return true
    }
    if len(a.ASPath) != len(b.ASPath) {
        return true
    }
    for i := range a.ASPath {
        if a.ASPath[i] != b.ASPath[i] {
            return true
        }
    }
    return false
}

func Build(routes []ingest.LoadedRoute, cfg policy.Config, tables map[string]guard.Tables) (FibDoc, LeakDoc) {
    byScenario := map[string]map[string][]ingest.LoadedRoute{}
    for _, r := range routes {
        if _, ok := byScenario[r.Scenario]; !ok {
            byScenario[r.Scenario] = map[string][]ingest.LoadedRoute{}
        }
        byScenario[r.Scenario][r.Prefix] = append(byScenario[r.Scenario][r.Prefix], r)
    }
    fib := FibDoc{}
    var leaks []LeakItem
    scenarios := make([]string, 0, len(byScenario))
    for s := range byScenario {
        scenarios = append(scenarios, s)
    }
    sort.Strings(scenarios)
    for _, sid := range scenarios {
        tab := tables[sid]
        prefixes := make([]string, 0, len(byScenario[sid]))
        for p := range byScenario[sid] {
            prefixes = append(prefixes, p)
        }
        sort.Strings(prefixes)
        for _, p := range prefixes {
            group := byScenario[sid][p]
            corrected := filterAdmit(group, cfg, tab, guard.Admit)
            baseline := filterAdmit(group, cfg, tab, stockAdmit)
            chosen := kernel.Pick_r7(corrected, cfg)
            shadow := kernel.Pick_r7(baseline, cfg)
            if chosen != nil {
                fib[sid] = append(fib[sid], FibEntry{
                    Prefix:  chosen.Prefix,
                    Peer:    chosen.Peer,
                    NextHop: chosen.NextHop,
                    ASPath:  chosen.ASPath,
                })
            }
            if routesDiffer(shadow, chosen) && shadow != nil {
                leaks = append(leaks, LeakItem{Prefix: shadow.Prefix, Peer: shadow.Peer, ASPath: shadow.ASPath})
            }
        }
    }
    sort.Slice(leaks, func(i, j int) bool {
        if leaks[i].Prefix != leaks[j].Prefix {
            return leaks[i].Prefix < leaks[j].Prefix
        }
        return leaks[i].Peer < leaks[j].Peer
    })
    return fib, LeakDoc{Items: leaks}
}

func WriteJSON(path string, v any) error {
    raw, err := json.MarshalIndent(v, "", "  ")
    if err != nil {
        return err
    }
    raw = append(raw, '\n')
    return os.WriteFile(path, raw, 0o644)
}
