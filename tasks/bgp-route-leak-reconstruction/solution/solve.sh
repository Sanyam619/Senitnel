#!/bin/bash
set -euo pipefail
cd /opt/bgplab

# Investigation pass: inspect the buggy admission surface before patching so
# the diagnosis is visible in the transcript.
echo '=== docs/format-notes.md ==='
sed -n '1,40p' docs/format-notes.md
echo '=== policy.toml ==='
cat data/policy.toml
echo '=== scenario layout ==='
ls data/scenarios
for s in data/scenarios/*/; do
    echo "-- $s --"
    ls "$s"
done
echo '=== internal/guard/load.go (compactRoa drops rows) ==='
cat internal/guard/load.go
echo '=== internal/guard/roa.go (origin uses path[0], prefix requires exact, cap is exclusive) ==='
cat internal/guard/roa.go
echo '=== internal/guard/revoke.go (picks lowest serial, same origin/prefix/cap bugs) ==='
cat internal/guard/revoke.go
echo '=== internal/guard/quarantine.go (filters on reason) ==='
cat internal/guard/quarantine.go
echo '=== shipped snapshot symptom ==='
mkdir -p /tmp/pre_out
bin/converge --policy data/policy.toml --scenarios data/scenarios --out /tmp/pre_out || true
echo "fib bundles before fix: $(python3 -c 'import json;print(len(json.load(open(\"/tmp/pre_out/fib.json\"))))')"
echo "leaks items before fix: $(python3 -c 'import json;print(len(json.load(open(\"/tmp/pre_out/leaks.json\"))[\"items\"]))')"

cat > internal/guard/load.go <<'GO'
package guard

import (
    "encoding/json"
    "os"
    "path/filepath"
    "sort"
)

func LoadTables(scenarioDir string) (Tables, error) {
    var out Tables
    roaRaw, err := os.ReadFile(filepath.Join(scenarioDir, "roa.json"))
    if err != nil {
        return Tables{}, err
    }
    if err := json.Unmarshal(roaRaw, &out.Roa); err != nil {
        return Tables{}, err
    }
    qRaw, err := os.ReadFile(filepath.Join(scenarioDir, "quarantine.json"))
    if err != nil {
        return Tables{}, err
    }
    if err := json.Unmarshal(qRaw, &out.Quarantine); err != nil {
        return Tables{}, err
    }
    orderRoaRows(&out.Roa)
    return out, nil
}

func orderRoaRows(doc *RoaDoc) {
    if len(doc.Entries) <= 1 {
        return
    }
    sort.Slice(doc.Entries, func(i, j int) bool {
        if doc.Entries[i].Prefix != doc.Entries[j].Prefix {
            return doc.Entries[i].Prefix < doc.Entries[j].Prefix
        }
        if doc.Entries[i].Serial != doc.Entries[j].Serial {
            return doc.Entries[i].Serial < doc.Entries[j].Serial
        }
        return doc.Entries[i].OriginASN < doc.Entries[j].OriginASN
    })
}
GO
cat > internal/guard/roa.go <<'GO'
package guard

import (
    "net"

    "bgplab/internal/ingest"
)

func originASN(path []int, peerAS int) int {
    if len(path) == 0 {
        return peerAS
    }
    return path[len(path)-1]
}

func prefixCovered(routePrefix, roaPrefix string) bool {
    if routePrefix == roaPrefix {
        return true
    }
    _, routeNet, err := net.ParseCIDR(routePrefix)
    if err != nil {
        return false
    }
    _, roaNet, err := net.ParseCIDR(roaPrefix)
    if err != nil {
        return false
    }
    roaOnes, _ := roaNet.Mask.Size()
    routeOnes, _ := routeNet.Mask.Size()
    if routeOnes < roaOnes {
        return false
    }
    mask := net.CIDRMask(roaOnes, 32)
    return routeNet.IP.Mask(mask).Equal(roaNet.IP.Mask(mask))
}

func MatchRoa(r ingest.LoadedRoute, doc RoaDoc) bool {
    if len(doc.Entries) == 0 {
        return true
    }
    origin := originASN(r.ASPath, r.PeerAS)
    var best *RoaEntry
    for _, row := range doc.Entries {
        if !prefixCovered(r.Prefix, row.Prefix) {
            continue
        }
        if row.OriginASN != origin {
            continue
        }
        if len(r.ASPath) > row.MaxLength {
            continue
        }
        if row.State != "valid" {
            continue
        }
        copy := row
        if best == nil || copy.Serial > best.Serial {
            best = &copy
        }
    }
    return best != nil
}
GO
cat > internal/guard/quarantine.go <<'GO'
package guard

import "bgplab/internal/ingest"

func Held(r ingest.LoadedRoute, doc QuarantineDoc) bool {
    for _, row := range doc.Holds {
        if row.Prefix == r.Prefix && row.Peer == r.Peer {
            return true
        }
    }
    return false
}
GO
cat > internal/guard/revoke.go <<'GO'
package guard

import "bgplab/internal/ingest"

func RevokeActive(r ingest.LoadedRoute, doc RoaDoc) bool {
    origin := originASN(r.ASPath, r.PeerAS)
    var newest *RoaEntry
    for _, row := range doc.Entries {
        if !prefixCovered(r.Prefix, row.Prefix) {
            continue
        }
        if row.OriginASN != origin {
            continue
        }
        if len(r.ASPath) > row.MaxLength {
            continue
        }
        copy := row
        if newest == nil || copy.Serial > newest.Serial {
            newest = &copy
        }
    }
    return newest != nil && newest.State == "valid"
}
GO
go build -o bin/converge ./cmd/converge
bin/converge --policy /opt/bgplab/data/policy.toml --scenarios /opt/bgplab/data/scenarios --out /output
