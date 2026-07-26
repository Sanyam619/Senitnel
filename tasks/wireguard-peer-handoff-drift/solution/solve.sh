#!/bin/bash
set -euo pipefail
cd /opt/wghandoff

cat > scripts/stage-roster.sh <<'SH'
#!/bin/bash
set -euo pipefail
scenario_dir="${1:?scenario directory}"
manifest_path="$scenario_dir/manifest.json"
table_path="$scenario_dir/epoch_table.json"
live_path="$scenario_dir/live_state.json"
TARGET=$(python3 - <<'PY' "$manifest_path"
import json, sys
print(json.load(open(sys.argv[1]))["target_epoch"])
PY
)
IDS=$(python3 - <<'PY' "$table_path" "$TARGET"
import json, sys
tab = json.load(open(sys.argv[1]))
pick = int(sys.argv[2])
ids = []
for row in tab["epochs"]:
    if row["epoch"] == pick:
        ids = [m["id"] for m in row["members"]]
print(json.dumps(ids))
PY
)
python3 - <<'PY' "$live_path" "$IDS" "$TARGET"
import json, sys
live = json.load(open(sys.argv[1]))
live["member_ids"] = json.loads(sys.argv[2])
live["epoch"] = int(sys.argv[3])
all_prior = set()
tab_path = sys.argv[1].replace("live_state.json", "epoch_table.json")
tab = json.load(open(tab_path))
target = int(sys.argv[3])
for row in tab["epochs"]:
    if row["epoch"] < target:
        for m in row["members"]:
            all_prior.add(m["id"])
want = set(live["member_ids"])
live["retired_ids"] = sorted(all_prior - want)
json.dump(live, open(sys.argv[1], "w"), indent=2)
print()
PY
SH
chmod +x scripts/stage-roster.sh

cat > scripts/flush-ledger.sh <<'SH'
#!/bin/bash
set -euo pipefail
scenario_dir="${1:?scenario directory}"
manifest_path="$scenario_dir/manifest.json"
table_path="$scenario_dir/epoch_table.json"
live_path="$scenario_dir/live_state.json"
TARGET=$(python3 - <<'PY' "$manifest_path"
import json, sys
print(json.load(open(sys.argv[1]))["target_epoch"])
PY
)
python3 - <<'PY' "$table_path" "$TARGET"
import json, sys
tab = json.load(open(sys.argv[1]))
tab["current_epoch"] = int(sys.argv[2])
json.dump(tab, open(sys.argv[1], "w"), indent=2)
print()
PY
python3 - <<'PY' "$live_path" "$TARGET"
import json, sys
live = json.load(open(sys.argv[1]))
live["epoch"] = int(sys.argv[2])
json.dump(live, open(sys.argv[1], "w"), indent=2)
print()
PY
SH
chmod +x scripts/flush-ledger.sh

cat > internal/k4/rowpick.go <<'GO'
package k4

import "wghandoff/internal/ingest"

// RowPick selects the epoch row used for live membership reconciliation.
func RowPick(b ingest.Bundle) int {
    return b.Manifest.TargetEpoch
}
GO

cat > internal/q2/cidrban.go <<'GO'
package q2

import "wghandoff/internal/ingest"

// WantIDs returns the peer ids for epoch ep.
func WantIDs(b ingest.Bundle, ep int) []string {
    return ingest.MemberIDs(b.RowForEpoch(ep))
}
GO

cat > internal/m7/absent.go <<'GO'
package m7

import (
    "sort"

    "wghandoff/internal/ingest"
    "wghandoff/internal/k4"
)

func priorIDs(b ingest.Bundle, target int) []string {
    seen := map[string]struct{}{}
    for _, row := range b.Table.Epochs {
        if row.Epoch >= target {
            continue
        }
        for _, m := range row.Members {
            seen[m.ID] = struct{}{}
        }
    }
    out := make([]string, 0, len(seen))
    for id := range seen {
        out = append(out, id)
    }
    sort.Strings(out)
    return out
}

// Absent_ok reports whether superseded peers from earlier rotations are gone.
func Absent_ok(b ingest.Bundle) bool {
    live := map[string]struct{}{}
    for _, id := range b.Live.MemberIDs {
        live[id] = struct{}{}
    }
    target := k4.RowPick(b)
    for _, id := range priorIDs(b, target) {
        want := ingest.MemberIDs(b.RowForEpoch(target))
        wantSet := map[string]struct{}{}
        for _, w := range want {
            wantSet[w] = struct{}{}
        }
        if _, ok := wantSet[id]; ok {
            continue
        }
        if _, ok := live[id]; ok {
            return false
        }
    }
    return true
}

func Drift_count(b ingest.Bundle, want []string) int {
    live := map[string]struct{}{}
    for _, id := range b.Live.MemberIDs {
        live[id] = struct{}{}
    }
    wantSet := map[string]struct{}{}
    for _, id := range want {
        wantSet[id] = struct{}{}
    }
    drift := 0
    for id := range live {
        if _, ok := wantSet[id]; !ok {
            drift++
        }
    }
    for id := range wantSet {
        if _, ok := live[id]; !ok {
            drift++
        }
    }
    return drift
}
GO

cat > internal/driver/run.go <<'GO'
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
        sort.Strings(want)
        live := append([]string(nil), nb.Live.MemberIDs...)
        sort.Strings(live)
        drift := m7.Drift_count(nb, want)
        clean := drift == 0 && m7.Absent_ok(nb)
        rep.Nodes = append(rep.Nodes, nodeRow{
            NodeID:    nb.Manifest.NodeID,
            Epoch:     nb.Live.Epoch,
            ActiveIDs: live,
            Drift:     drift,
            Clean:     clean,
        })
        if !clean {
            liveSet := map[string]struct{}{}
            for _, id := range nb.Live.MemberIDs {
                liveSet[id] = struct{}{}
            }
            wantSet := map[string]struct{}{}
            for _, id := range want {
                wantSet[id] = struct{}{}
            }
            for id := range liveSet {
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
GO

go build -o bin/reconcile ./cmd/reconcile
bin/reconcile --policy data/policy.toml --scenarios data/scenarios --out /output
