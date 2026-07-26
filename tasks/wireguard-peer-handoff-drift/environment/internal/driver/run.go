package driver

import (
    "encoding/json"
    "os"
    "os/exec"
    "path/filepath"
    "sort"

    "wghandoff/internal/ingest"
    "wghandoff/internal/k4"
    "wghandoff/internal/m7"
    "wghandoff/internal/q2"
)

type driftRow struct {
    NodeID  string `json:"node_id"`
    StaleID string `json:"stale_id"`
    Reason  string `json:"reason"`
}

type nodeRow struct {
    NodeID    string   `json:"node_id"`
    Epoch     int      `json:"epoch"`
    ActiveIDs []string `json:"active_ids"`
    Drift     int      `json:"drift"`
    Clean     bool     `json:"clean"`
}

type report struct {
    Version int        `json:"version"`
    Nodes   []nodeRow  `json:"nodes"`
    Drifts  []driftRow `json:"drifts"`
}

func Run(policyPath, scenarioRoot, outDir string) error {
    _ = policyPath
    bundles, err := ingest.ListBundles(scenarioRoot)
    if err != nil {
        return err
    }
    root := filepath.Dir(filepath.Dir(scenarioRoot))
    apply := filepath.Join(root, "scripts", "stage-roster.sh")
    sync := filepath.Join(root, "scripts", "flush-ledger.sh")
    rep := report{Version: 1, Drifts: []driftRow{}}
    for _, b := range bundles {
        if err := exec.Command(apply, b.Dir).Run(); err != nil {
            return err
        }
        if err := exec.Command(sync, b.Dir).Run(); err != nil {
            return err
        }
        nb, err := ingest.LoadBundle(b.Dir)
        if err != nil {
            return err
        }
        ep := k4.RowPick(nb)
        want := q2.WantIDs(nb, ep)
        drift := m7.Drift_count(nb, want)
        clean := drift == 0 && m7.Absent_ok(nb)
        rep.Nodes = append(rep.Nodes, nodeRow{
            NodeID:    nb.Manifest.NodeID,
            Epoch:     nb.Live.Epoch,
            ActiveIDs: append([]string(nil), nb.Live.MemberIDs...),
            Drift:     drift,
            Clean:     clean,
        })
        sort.Strings(rep.Nodes[len(rep.Nodes)-1].ActiveIDs)
        if !clean {
            live := map[string]struct{}{}
            for _, id := range nb.Live.MemberIDs {
                live[id] = struct{}{}
            }
            wantSet := map[string]struct{}{}
            for _, id := range want {
                wantSet[id] = struct{}{}
            }
            for id := range live {
                if _, ok := wantSet[id]; !ok {
                    rep.Drifts = append(rep.Drifts, driftRow{
                        NodeID:  nb.Manifest.NodeID,
                        StaleID: id,
                        Reason:  "unexpected_live",
                    })
                }
            }
        }
    }
    sort.Slice(rep.Nodes, func(i, j int) bool {
        return rep.Nodes[i].NodeID < rep.Nodes[j].NodeID
    })
    sort.Slice(rep.Drifts, func(i, j int) bool {
        if rep.Drifts[i].NodeID != rep.Drifts[j].NodeID {
            return rep.Drifts[i].NodeID < rep.Drifts[j].NodeID
        }
        return rep.Drifts[i].StaleID < rep.Drifts[j].StaleID
    })
    if err := os.MkdirAll(outDir, 0o755); err != nil {
        return err
    }
    raw, err := json.MarshalIndent(rep, "", "  ")
    if err != nil {
        return err
    }
    raw = append(raw, 0x0a)
    return os.WriteFile(filepath.Join(outDir, "handoff_report.json"), raw, 0o644)
}
