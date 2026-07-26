#!/usr/bin/env python3
"""Generate tasks/wireguard-peer-handoff-drift (authoring tool, not shipped)."""
from __future__ import annotations

import json
import subprocess
import textwrap
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "tasks" / "wireguard-peer-handoff-drift"
ENV = TASK / "environment"
TASK_ROOT = "/opt/wghandoff"
OUTPUT_ROOT = "/output"


@dataclass
class Member:
    mid: str
    pubkey: str
    endpoint: str
    allowed: list[str]


@dataclass
class Scenario:
    node_id: str
    target_epoch: int
    epochs: dict[int, list[Member]]
    runtime_epoch: int
    runtime_members: list[str]
    ledger_epoch: int
    pending_epoch: int | None = None
    pending_member_epoch: int | None = None


SCENARIOS: list[Scenario] = [
    Scenario(
        node_id="alpha",
        target_epoch=3,
        epochs={
            1: [
                Member("m-a1", "pkA1aa", "203.0.113.10:51820", ["10.10.1.0/24"]),
            ],
            2: [
                Member("m-a2", "pkA2bb", "203.0.113.11:51820", ["10.10.2.0/24"]),
                Member("m-a3", "pkA3cc", "203.0.113.12:51820", ["10.10.3.0/24"]),
            ],
            3: [
                Member("m-a4", "pkA4dd", "203.0.113.13:51820", ["10.10.4.0/24"]),
                Member("m-a5", "pkA5ee", "203.0.113.14:51820", ["10.10.5.0/24"]),
            ],
        },
        runtime_epoch=2,
        runtime_members=["m-a1", "m-a4", "m-a5"],
        ledger_epoch=3,
    ),
    Scenario(
        node_id="bravo",
        target_epoch=2,
        epochs={
            1: [
                Member("m-b1", "pkB1aa", "203.0.113.20:51820", ["10.20.1.0/24"]),
                Member("m-b2", "pkB2bb", "203.0.113.21:51820", ["10.20.2.0/24"]),
            ],
            2: [
                Member("m-b3", "pkB3cc", "203.0.113.22:51820", ["10.20.3.0/24"]),
            ],
        },
        runtime_epoch=1,
        runtime_members=["m-b1", "m-b2", "m-b3"],
        ledger_epoch=2,
    ),
    Scenario(
        node_id="charlie",
        target_epoch=4,
        epochs={
            1: [Member("m-c1", "pkC1aa", "203.0.113.30:51820", ["10.30.1.0/24"])],
            2: [Member("m-c2", "pkC2bb", "203.0.113.31:51820", ["10.30.2.0/24"])],
            3: [Member("m-c3", "pkC3cc", "203.0.113.32:51820", ["10.30.3.0/24"])],
            4: [
                Member("m-c4", "pkC4dd", "203.0.113.33:51820", ["10.30.4.0/24"]),
                Member("m-c5", "pkC5ee", "203.0.113.34:51820", ["10.30.5.0/24"]),
            ],
        },
        runtime_epoch=3,
        runtime_members=["m-c2", "m-c4", "m-c5"],
        ledger_epoch=4,
    ),
    Scenario(
        node_id="delta",
        target_epoch=2,
        epochs={
            1: [
                Member("m-d1", "pkD1aa", "203.0.113.40:51820", ["10.40.1.0/24"]),
            ],
            2: [
                Member("m-d2", "pkD2bb", "203.0.113.41:51820", ["10.40.2.0/24"]),
                Member("m-d3", "pkD3cc", "203.0.113.42:51820", ["10.40.3.0/24"]),
            ],
        },
        runtime_epoch=2,
        runtime_members=["m-d1", "m-d2", "m-d3"],
        ledger_epoch=2,
    ),
    Scenario(
        node_id="echo",
        target_epoch=4,
        epochs={
            1: [Member("m-e1", "pkE1aa", "203.0.113.50:51820", ["10.50.1.0/24"])],
            2: [Member("m-e2", "pkE2bb", "203.0.113.51:51820", ["10.50.2.0/24"])],
            3: [Member("m-e3", "pkE3cc", "203.0.113.52:51820", ["10.50.3.0/24"])],
            4: [
                Member("m-e4", "pkE4dd", "203.0.113.53:51820", ["10.50.4.0/24"]),
                Member("m-e5", "pkE5ee", "203.0.113.54:51820", ["10.50.5.0/24"]),
            ],
        },
        runtime_epoch=3,
        runtime_members=["m-e2", "m-e4", "m-e5"],
        ledger_epoch=4,
        pending_epoch=2,
    ),
    Scenario(
        node_id="foxtrot",
        target_epoch=3,
        epochs={
            1: [Member("m-f1", "pkF1aa", "203.0.113.60:51820", ["10.60.1.0/24"])],
            2: [Member("m-f2", "pkF2bb", "203.0.113.61:51820", ["10.60.2.0/24"])],
            3: [
                Member("m-f3", "pkF3cc", "203.0.113.62:51820", ["10.60.3.0/24"]),
                Member("m-f4", "pkF4dd", "203.0.113.63:51820", ["10.60.4.0/24"]),
            ],
        },
        runtime_epoch=2,
        runtime_members=["m-f1", "m-f2", "m-f3"],
        ledger_epoch=3,
        pending_epoch=3,
        pending_member_epoch=2,
    ),
    Scenario(
        node_id="golf",
        target_epoch=3,
        epochs={
            1: [Member("m-g1", "pkG1aa", "203.0.113.70:51820", ["10.70.1.0/24"])],
            2: [Member("m-g2", "pkG2bb", "203.0.113.71:51820", ["10.70.2.0/24"])],
            3: [
                Member("m-g3", "pkG3cc", "203.0.113.72:51820", ["10.70.1.0/24"]),
                Member("m-g4", "pkG4dd", "203.0.113.73:51820", ["10.70.3.0/24"]),
            ],
        },
        runtime_epoch=2,
        runtime_members=["m-g1", "m-g2"],
        ledger_epoch=2,
        pending_epoch=3,
    ),
    Scenario(
        node_id="hotel",
        target_epoch=3,
        epochs={
            1: [Member("m-h1", "pkH1aa", "203.0.113.80:51820", ["10.80.1.0/24"])],
            2: [
                Member("m-h2", "pkH2bb", "203.0.113.81:51820", ["10.80.2.0/24"]),
                Member("m-h3", "pkH3cc", "203.0.113.82:51820", ["10.80.3.0/24"]),
            ],
            3: [
                Member("m-h2", "pkH2bb", "203.0.113.81:51820", ["10.80.2.0/24"]),
                Member("m-h4", "pkH4dd", "203.0.113.83:51820", ["10.80.4.0/24"]),
            ],
        },
        runtime_epoch=2,
        runtime_members=["m-h2", "m-h3"],
        ledger_epoch=3,
    ),
]


def w(rel: str, content: str) -> None:
    p = TASK / rel if not rel.startswith("environment/") else ENV / rel.removeprefix("environment/")
    p.parent.mkdir(parents=True, exist_ok=True)
    text = textwrap.dedent(content).lstrip("\n")
    text = text.replace("{TASK_ROOT}", TASK_ROOT).replace("{OUTPUT_ROOT}", OUTPUT_ROOT)
    p.write_text(text, encoding="utf-8")


def member_dict(m: Member) -> dict:
    return {
        "id": m.mid,
        "pubkey": m.pubkey,
        "endpoint": m.endpoint,
        "allowed_ips": m.allowed,
    }


def expected_active(sc: Scenario) -> list[str]:
    rows = sc.epochs[sc.target_epoch]
    return sorted(m.mid for m in rows)


def prior_members(sc: Scenario) -> set[str]:
    out: set[str] = set()
    for ep in range(1, sc.target_epoch):
        for m in sc.epochs.get(ep, []):
            out.add(m.mid)
    return out


def compute_gt() -> tuple[dict, dict]:
    nodes = []
    drifts: list[dict] = []
    for sc in SCENARIOS:
        active = expected_active(sc)
        nodes.append(
            {
                "node_id": sc.node_id,
                "epoch": sc.target_epoch,
                "active_ids": active,
                "drift": 0,
                "clean": True,
            }
        )
    nodes.sort(key=lambda r: r["node_id"])
    return {"version": 1, "nodes": nodes, "drifts": drifts}, {"version": 1, "nodes": nodes, "drifts": drifts}


REPORT_GT, _ = compute_gt()


def write_scenarios() -> None:
    index: dict[str, dict] = {}
    for sc in SCENARIOS:
        base = ENV / "data" / "scenarios" / sc.node_id
        epoch_rows = []
        for ep in sorted(sc.epochs):
            epoch_rows.append(
                {
                    "epoch": ep,
                    "members": [member_dict(m) for m in sc.epochs[ep]],
                }
            )
        w(
            f"environment/data/scenarios/{sc.node_id}/manifest.json",
            json.dumps(
                {"node_id": sc.node_id, "target_epoch": sc.target_epoch},
                indent=2,
            )
            + "\n",
        )
        w(
            f"environment/data/scenarios/{sc.node_id}/epoch_table.json",
            json.dumps(
                {"current_epoch": sc.ledger_epoch, "epochs": epoch_rows},
                indent=2,
            )
            + "\n",
        )
        retired = sorted(prior_members(sc) - set(expected_active(sc)))
        w(
            f"environment/data/scenarios/{sc.node_id}/live_state.json",
            json.dumps(
                {
                    "epoch": sc.runtime_epoch,
                    "member_ids": sc.runtime_members,
                    "retired_ids": retired,
                },
                indent=2,
            )
            + "\n",
        )
        pending_ep = sc.pending_epoch if sc.pending_epoch is not None else sc.target_epoch
        pending_src = (
            sc.pending_member_epoch if sc.pending_member_epoch is not None else sc.target_epoch
        )
        pending_members = sc.epochs[pending_src]
        w(
            f"environment/data/scenarios/{sc.node_id}/pending.json",
            json.dumps(
                {
                    "epoch": pending_ep,
                    "member_ids": [m.mid for m in pending_members],
                },
                indent=2,
            )
            + "\n",
        )
        index[sc.node_id] = {"target_epoch": sc.target_epoch}
    w(
        "environment/data/scenarios/bundle_index.json",
        json.dumps({"bundles": index}, indent=2) + "\n",
    )


def write_go_sources() -> None:
    w(
        "environment/go.mod",
        """
        module wghandoff

        go 1.22
        """,
    )

    w(
        "environment/cmd/reconcile/main.go",
        """
        // handoff_report.json schema (written to --out):
        //
        // version — integer, must be 1
        // nodes — array sorted by node_id ascending; each row has:
        //   node_id — string scenario name
        //   epoch — integer active epoch after reconcile (must match manifest target_epoch)
        //   active_ids — sorted string array of member ids live on the node
        //   drift — integer count of stale members still present (zero when reconciled)
        //   clean — boolean, true when drift is zero and truly retired peers are absent
        //           (carry-forward peers that remain in the target roster may stay live)
        // drifts — array of violation rows sorted by node_id then stale_id; empty when reconciled
        //   each row: node_id, stale_id, reason (string)
        //
        package main

        import (
            "flag"
            "log"

            "wghandoff/internal/driver"
        )

        func main() {
            policy := flag.String("policy", "", "policy toml")
            scenarios := flag.String("scenarios", "", "scenario root")
            out := flag.String("out", "", "output directory")
            flag.Parse()
            if *policy == "" || *scenarios == "" || *out == "" {
                log.Fatal("usage: reconcile --policy PATH --scenarios PATH --out PATH")
            }
            if err := driver.Run(*policy, *scenarios, *out); err != nil {
                log.Fatal(err)
            }
        }
        """,
    )

    w(
        "environment/internal/ingest/load.go",
        """
        package ingest

        import (
            "encoding/json"
            "os"
            "path/filepath"
            "sort"
        )

        type Member struct {
            ID         string   `json:"id"`
            Pubkey     string   `json:"pubkey"`
            Endpoint   string   `json:"endpoint"`
            AllowedIPs []string `json:"allowed_ips"`
        }

        type EpochRow struct {
            Epoch   int      `json:"epoch"`
            Members []Member `json:"members"`
        }

        type EpochTable struct {
            CurrentEpoch int        `json:"current_epoch"`
            Epochs       []EpochRow `json:"epochs"`
        }

        type LiveState struct {
            Epoch      int      `json:"epoch"`
            MemberIDs  []string `json:"member_ids"`
            RetiredIDs []string `json:"retired_ids"`
        }

        type Manifest struct {
            NodeID      string `json:"node_id"`
            TargetEpoch int    `json:"target_epoch"`
        }

        type Pending struct {
            Epoch     int      `json:"epoch"`
            MemberIDs []string `json:"member_ids"`
        }

        type Bundle struct {
            Dir     string
            Manifest Manifest
            Table   EpochTable
            Live    LiveState
            Pending Pending
        }

        func LoadBundle(dir string) (Bundle, error) {
            var b Bundle
            b.Dir = dir
            if err := readJSON(filepath.Join(dir, "manifest.json"), &b.Manifest); err != nil {
                return b, err
            }
            if err := readJSON(filepath.Join(dir, "epoch_table.json"), &b.Table); err != nil {
                return b, err
            }
            if err := readJSON(filepath.Join(dir, "live_state.json"), &b.Live); err != nil {
                return b, err
            }
            if err := readJSON(filepath.Join(dir, "pending.json"), &b.Pending); err != nil {
                return b, err
            }
            return b, nil
        }

        func ListBundles(root string) ([]Bundle, error) {
            entries, err := os.ReadDir(root)
            if err != nil {
                return nil, err
            }
            names := make([]string, 0, len(entries))
            for _, e := range entries {
                if e.IsDir() {
                    names = append(names, e.Name())
                }
            }
            sort.Strings(names)
            out := make([]Bundle, 0, len(names))
            for _, name := range names {
                b, err := LoadBundle(filepath.Join(root, name))
                if err != nil {
                    return nil, err
                }
                out = append(out, b)
            }
            return out, nil
        }

        func readJSON(path string, v any) error {
            raw, err := os.ReadFile(path)
            if err != nil {
                return err
            }
            return json.Unmarshal(raw, v)
        }

        func (b Bundle) RowForEpoch(ep int) []Member {
            for _, row := range b.Table.Epochs {
                if row.Epoch == ep {
                    return row.Members
                }
            }
            return nil
        }

        func MemberIDs(ms []Member) []string {
            ids := make([]string, 0, len(ms))
            for _, m := range ms {
                ids = append(ids, m.ID)
            }
            sort.Strings(ids)
            return ids
        }
        """,
    )

    w(
        "environment/internal/k4/rowpick.go",
        """
        package k4

        import "wghandoff/internal/ingest"

        // RowPick selects the epoch row used for live membership reconciliation.
        func RowPick(b ingest.Bundle) int {
            if b.Pending.Epoch == b.Table.CurrentEpoch && b.Pending.Epoch > 0 {
                return b.Pending.Epoch
            }
            if b.Live.Epoch > 0 {
                return b.Live.Epoch
            }
            return b.Table.CurrentEpoch
        }
        """,
    )

    w(
        "environment/internal/q2/cidrban.go",
        """
        package q2

        import (
            "sort"

            "wghandoff/internal/ingest"
        )

        // WantIDs returns the peer ids for epoch ep.
        func WantIDs(b ingest.Bundle, ep int) []string {
            reserved := map[string]struct{}{}
            for _, row := range b.Table.Epochs {
                if row.Epoch >= ep {
                    continue
                }
                for _, m := range row.Members {
                    for _, cidr := range m.AllowedIPs {
                        reserved[cidr] = struct{}{}
                    }
                }
            }
            out := make([]string, 0)
            for _, m := range b.RowForEpoch(ep) {
                blocked := false
                for _, cidr := range m.AllowedIPs {
                    if _, ok := reserved[cidr]; ok {
                        blocked = true
                        break
                    }
                }
                if !blocked {
                    out = append(out, m.ID)
                }
            }
            sort.Strings(out)
            return out
        }
        """,
    )

    w(
        "environment/internal/m7/absent.go",
        """
        package m7

        import "wghandoff/internal/ingest"

        // Absent_ok reports whether superseded peers from earlier rotations are gone.
        func Absent_ok(b ingest.Bundle) bool {
            live := map[string]struct{}{}
            for _, id := range b.Live.MemberIDs {
                live[id] = struct{}{}
            }
            for _, row := range b.Table.Epochs {
                if row.Epoch >= b.Manifest.TargetEpoch {
                    continue
                }
                for _, m := range row.Members {
                    if _, ok := live[m.ID]; ok {
                        return false
                    }
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
            return drift
        }
        """,
    )

    w(
        "environment/internal/n3/shadow.go",
        """
        package n3

        import "wghandoff/internal/ingest"

        // ShadowPick mirrors row selection for the decoy audit path.
        func ShadowPick(b ingest.Bundle) int {
            if b.Live.Epoch > 0 {
                return b.Live.Epoch
            }
            return b.Table.CurrentEpoch
        }

        func ShadowIDs(b ingest.Bundle, ep int) []string {
            return ingest.MemberIDs(b.RowForEpoch(ep))
        }
        """,
    )

    w(
        "environment/internal/r6/queueview.go",
        """
        package r6

        import "wghandoff/internal/ingest"

        // QueueIDs mirrors the pending queue for audit tooling.
        func QueueIDs(b ingest.Bundle) []string {
            return append([]string(nil), b.Pending.MemberIDs...)
        }

        func QueueEpoch(b ingest.Bundle) int {
            return b.Pending.Epoch
        }
        """,
    )

    w(
        "environment/internal/p9/ledger.go",
        """
        package p9

        import "wghandoff/internal/ingest"

        func LedgerEpoch(b ingest.Bundle) int {
            return b.Table.CurrentEpoch
        }

        func LiveEpoch(b ingest.Bundle) int {
            return b.Live.Epoch
        }

        func PendingEpoch(b ingest.Bundle) int {
            return b.Pending.Epoch
        }
        """,
    )

    w(
        "environment/internal/driver/run.go",
        """
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
        """,
    )

    w(
        "environment/scripts/stage-roster.sh",
        """\
        #!/bin/bash
        set -euo pipefail
        SCENARIO="${1:?scenario directory}"
        LIVE="$SCENARIO/live_state.json"
        PENDING="$SCENARIO/pending.json"
        python3 - <<'PY' "$LIVE" "$PENDING"
        import json, sys
        live = json.load(open(sys.argv[1]))
        pending = json.load(open(sys.argv[2]))
        merged = sorted(set(live.get("member_ids", [])) | set(pending.get("member_ids", [])))
        live["member_ids"] = merged
        json.dump(live, open(sys.argv[1], "w"), indent=2)
        print()
        PY
        """,
    )

    w(
        "environment/scripts/flush-ledger.sh",
        """\
        #!/bin/bash
        set -euo pipefail
        SCENARIO="${1:?scenario directory}"
        TABLE="$SCENARIO/epoch_table.json"
        LIVE="$SCENARIO/live_state.json"
        python3 - <<'PY' "$TABLE" "$LIVE"
        import json, sys
        tab = json.load(open(sys.argv[1]))
        live = json.load(open(sys.argv[2]))
        tab["current_epoch"] = live["epoch"]
        json.dump(tab, open(sys.argv[1], "w"), indent=2)
        print()
        PY
        """,
    )

    w(
        "environment/scripts/audit-roster.sh",
        """\
        #!/bin/bash
        set -euo pipefail
        SCENARIO="${1:?scenario directory}"
        TABLE="$SCENARIO/epoch_table.json"
        LIVE="$SCENARIO/live_state.json"
        PICK=$(python3 - <<'PY' "$LIVE"
        import json, sys
        live = json.load(open(sys.argv[1]))
        print(live.get("epoch", 0))
        PY
        )
        IDS=$(python3 - <<'PY' "$TABLE" "$PICK"
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
        python3 - <<'PY' "$LIVE" "$IDS"
        import json, sys
        live = json.load(open(sys.argv[1]))
        live["member_ids"] = json.loads(sys.argv[2])
        json.dump(live, open(sys.argv[1], "w"), indent=2)
        print()
        PY
        """,
    )

    w(
        "environment/scripts/smoke.sh",
        """\
        #!/bin/bash
        set -euo pipefail
        cd {TASK_ROOT}
        go build -o bin/reconcile ./cmd/reconcile
        bin/reconcile --policy data/policy.toml --scenarios data/scenarios --out /tmp/wg-smoke-out
        test -s /tmp/wg-smoke-out/handoff_report.json
        """,
    )

    w(
        "environment/data/policy.toml",
        """
        [lab]
        scenario_root = "data/scenarios"
        report_name = "handoff_report.json"

        [cutover]
        epoch_authority = "manifest"
        roster_source = "epoch_table"
        staging_mode = "replace"
        allow_cidr_reuse = true
        """,
    )

    w(
        "environment/config/paths.toml",
        """
        reconcile_bin = "bin/reconcile"
        scenario_root = "data/scenarios"
        output_root = "/output"
        """,
    )

    w(
        "environment/docs/operator-notes.md",
        """
        WireGuard edge handoff lab ({TASK_ROOT})

        Fleet operators rotate allowed peer rosters on edge nodes through numbered
        epochs. Each rotation promotes a new member set; peers that no longer appear
        in the target epoch must leave the live tunnel. A peer that appears in both
        the prior epoch and the target epoch is a carry-forward and must remain.

        Authority chain (see also data/policy.toml [cutover]):
          epoch_authority = manifest   — target_epoch is the cutover destination
          roster_source = epoch_table  — member ids for an epoch come from that row
          staging_mode = replace       — wire roster is replaced, not merged with queue
          allow_cidr_reuse = true      — AllowedIPs from retired epochs may be reused

        Bundle layout under data/scenarios/<node_id>/:
          manifest.json     — desired cutover epoch (target_epoch)
          epoch_table.json  — historical roster rows keyed by epoch plus ledger counter
          live_state.json   — on-wire snapshot: epoch, member_ids, retired_ids
          pending.json      — automation queue left by the last staging pass (may lag)

        bundle_index.json lists every lab node and its target_epoch. Operator scripts
        under scripts/ mutate live_state.json and epoch_table.json inside each bundle.
        bin/reconcile walks all bundles, runs those scripts, validates membership, and
        writes handoff_report.json. Field semantics for the report are documented in
        cmd/reconcile/main.go.
        """,
    )


def write_task_meta() -> None:
    w(
        "task.toml",
        """
        version = "2.0"

        [metadata]
        author_name = "anonymous"
        author_email = "anonymous"
        difficulty = "hard"
        category = "security"
        subcategories = ["tool_specific"]
        number_of_milestones = 0
        codebase_size = "small"
        languages = ["go", "bash"]
        tags = ["wireguard", "vpn", "handoff", "go", "bash", "ops"]
        expert_time_estimate_min = 180
        junior_time_estimate_min = 360

        [verifier]
        timeout_sec = 600

        [agent]
        timeout_sec = 1200

        [environment]
        allow_internet = false
        build_timeout_sec = 600
        cpus = 2
        memory_mb = 4096
        storage_mb = 10240
        gpus = 0
        gpu_types = []
        docker_flags = []
        """,
    )
    w(
        "output_contract.toml",
        """
        user_visible_outputs = [
          "{OUTPUT_ROOT}/handoff_report.json",
          "{TASK_ROOT}/bin/reconcile",
        ]

        internal_harness_files = [
          "{TASK_ROOT}/scripts/stage-roster.sh",
          "{TASK_ROOT}/scripts/flush-ledger.sh",
        ]

        [structured_outputs.handoff_report]
        target = "{OUTPUT_ROOT}/handoff_report.json"
        format = "json"
        instruction_checks = [
          "version",
          "nodes",
          "node_id",
          "epoch",
          "active_ids",
          "drift",
          "clean",
          "drifts",
          "stale_id",
          "reason",
        ]
        """,
    )
    w(
        "instruction.md",
        """
        The edge fleet under {TASK_ROOT}/data/scenarios/ runs WireGuard peer rotations through numbered epochs. Each node bundle holds an epoch history, an operator manifest with the desired cutover epoch, an on-wire live snapshot, and a pending automation queue that may disagree with the manifest. {TASK_ROOT}/docs/operator-notes.md describes the bundle layout and the cutover authority rules in {TASK_ROOT}/data/policy.toml. {TASK_ROOT}/data/scenarios/bundle_index.json lists the fleet.

        The lab is inconsistent after an overnight rotation window. {TASK_ROOT}/bin/reconcile exits zero and writes {OUTPUT_ROOT}/handoff_report.json. Noc still sees mixed-epoch peer sets, ledger counters that disagree with the wire epoch, pending queues whose epoch labels or member lists disagree with the manifest, carry-forward peers mishandled relative to truly retired peers, and AllowedIPs from retired epochs treated as permanently reserved despite allow_cidr_reuse in policy.

        A consistent post-cutover picture is required. handoff_report.json (version 1) has a nodes array listing every node at its manifest target_epoch with active_ids equal to that epoch's member identifiers in ascending order, drift zero, clean true, and an empty drifts array with no stale_id or reason entries. Node rows sort by node_id; repeated runs are byte-identical. Report field semantics and CLI flags are in the comment block above main in {TASK_ROOT}/cmd/reconcile/main.go. Scenario fixtures under {TASK_ROOT}/data/scenarios/ are read-only inputs.
        """,
    )
    w(
        "tests/test.sh",
        """
        #!/bin/bash

        # Verifier dependencies are installed in environment/Dockerfile.
        # Add task-specific verifier-only Python packages there, not here.

        mkdir -p /logs/verifier

        if [ "$PWD" = "/" ]; then
            echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile before running this script."
            echo 0 > /logs/verifier/reward.txt
            exit 1
        fi

        python3 -m pytest -o cache_dir=/tmp/pytest_cache \\
          --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA

        if [ $? -eq 0 ]; then
            echo 1 > /logs/verifier/reward.txt
        else
            echo 0 > /logs/verifier/reward.txt
        fi
        """,
    )


def write_tests() -> None:
    body = f'''"""Verifier tests for WireGuard peer handoff reconcile output."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

OPT = Path("{TASK_ROOT}")
OUT = Path("{OUTPUT_ROOT}")
RECONCILE = OPT / "bin" / "reconcile"
SCENARIO_ROOT = OPT / "data" / "scenarios"
BUNDLE_INDEX = SCENARIO_ROOT / "bundle_index.json"
REPORT_PATH = OUT / "handoff_report.json"


def load_bundle_index():
    return json.loads(BUNDLE_INDEX.read_text(encoding="utf-8"))["bundles"]


def load_manifest(node_id: str) -> dict:
    return json.loads(
        (SCENARIO_ROOT / node_id / "manifest.json").read_text(encoding="utf-8")
    )


def load_epoch_table(node_id: str) -> dict:
    return json.loads(
        (SCENARIO_ROOT / node_id / "epoch_table.json").read_text(encoding="utf-8")
    )


def target_member_ids(node_id: str) -> list[str]:
    manifest = load_manifest(node_id)
    table = load_epoch_table(node_id)
    target = manifest["target_epoch"]
    active = []
    for row in table["epochs"]:
        if row["epoch"] == target:
            active = sorted(m["id"] for m in row["members"])
    return active


def prior_retired_ids(node_id: str) -> set[str]:
    manifest = load_manifest(node_id)
    table = load_epoch_table(node_id)
    target = manifest["target_epoch"]
    target_set = set(target_member_ids(node_id))
    prior = set()
    for row in table["epochs"]:
        if row["epoch"] < target:
            for m in row["members"]:
                prior.add(m["id"])
    return prior - target_set


def expected_node_row(node_id: str) -> dict:
    manifest = load_manifest(node_id)
    return {{
        "node_id": node_id,
        "epoch": manifest["target_epoch"],
        "active_ids": target_member_ids(node_id),
        "drift": 0,
        "clean": True,
    }}


def expected_report() -> dict:
    nodes = [expected_node_row(node_id) for node_id in sorted(load_bundle_index())]
    return {{"version": 1, "nodes": nodes, "drifts": []}}


def run_tool():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    subprocess.run(
        ["go", "build", "-o", "bin/reconcile", "./cmd/reconcile"],
        check=True,
        cwd=OPT,
        timeout=120,
    )
    subprocess.run(
        [
            str(RECONCILE),
            "--policy",
            str(OPT / "data" / "policy.toml"),
            "--scenarios",
            str(OPT / "data" / "scenarios"),
            "--out",
            str(OUT),
        ],
        check=True,
        cwd=OPT,
        timeout=120,
    )
    return json.loads(REPORT_PATH.read_text())


@pytest.fixture(scope="module")
def report():
    return run_tool()


def test_report_exists(report):
    """handoff_report.json is written to the instructed output path."""
    assert REPORT_PATH.is_file()
    assert report["version"] == 1


def test_report_trailing_newline(report):
    """Report file ends with a single trailing newline."""
    raw = REPORT_PATH.read_bytes()
    assert raw.endswith(b"\\n")
    assert not raw.endswith(b"\\n\\n")


def test_bundle_count(report):
    """Report row count matches the bundle index fleet size."""
    assert len(report["nodes"]) == len(load_bundle_index())


def test_all_nodes_present(report):
    """Report covers every scenario bundle."""
    expected = set(load_bundle_index())
    assert {{r["node_id"] for r in report["nodes"]}} == expected


def test_nodes_sorted(report):
    """Node rows appear in ascending node_id order."""
    ids = [row["node_id"] for row in report["nodes"]]
    assert ids == sorted(ids)


def test_active_ids_sorted(report):
    """Each node lists active_ids in ascending order."""
    for row in report["nodes"]:
        assert row["active_ids"] == sorted(row["active_ids"])


def test_all_nodes_zero_drift(report):
    """Every node reports zero membership drift after reconcile."""
    assert all(row["drift"] == 0 for row in report["nodes"])


def test_all_nodes_clean(report):
    """Every node reports clean true after reconcile."""
    assert all(row["clean"] is True for row in report["nodes"])


def test_epoch_matches_manifest_target(report):
    """Each node epoch field matches its manifest target_epoch."""
    for row in report["nodes"]:
        manifest = load_manifest(row["node_id"])
        assert row["epoch"] == manifest["target_epoch"]


def test_active_ids_match_target_epoch_row(report):
    """active_ids equals the target epoch roster from epoch_table.json."""
    for row in report["nodes"]:
        assert row["active_ids"] == target_member_ids(row["node_id"])


def test_no_retired_peer_on_wire(report):
    """Superseded peers from earlier epochs do not survive on the wire."""
    for row in report["nodes"]:
        stale = prior_retired_ids(row["node_id"])
        live = set(row["active_ids"])
        assert live.isdisjoint(stale)


def test_alpha_epoch(report):
    """Alpha reaches target epoch three with only m-a4 and m-a5 live."""
    row = next(r for r in report["nodes"] if r["node_id"] == "alpha")
    assert row == expected_node_row("alpha")


def test_bravo_clean(report):
    """Bravo finishes on epoch two with sole member m-b3."""
    row = next(r for r in report["nodes"] if r["node_id"] == "bravo")
    assert row == expected_node_row("bravo")


def test_charlie_members(report):
    """Charlie lands epoch four with m-c4 and m-c5 only."""
    row = next(r for r in report["nodes"] if r["node_id"] == "charlie")
    assert row == expected_node_row("charlie")


def test_delta_no_stale(report):
    """Delta drops retired m-d1 and keeps m-d2 and m-d3."""
    row = next(r for r in report["nodes"] if r["node_id"] == "delta")
    assert row == expected_node_row("delta")


def test_echo_pending_lag(report):
    """Echo reaches epoch four despite a stale pending queue epoch label."""
    row = next(r for r in report["nodes"] if r["node_id"] == "echo")
    assert row == expected_node_row("echo")
    pending = json.loads(
        (SCENARIO_ROOT / "echo" / "pending.json").read_text(encoding="utf-8")
    )
    manifest = load_manifest("echo")
    assert pending["epoch"] != manifest["target_epoch"]


def test_foxtrot_queue_roster_mismatch(report):
    """Foxtrot promotes epoch-three roster m-f3 and m-f4, not the queued epoch-two peer."""
    row = next(r for r in report["nodes"] if r["node_id"] == "foxtrot")
    assert row == expected_node_row("foxtrot")
    pending = json.loads(
        (SCENARIO_ROOT / "foxtrot" / "pending.json").read_text(encoding="utf-8")
    )
    assert pending["epoch"] == load_manifest("foxtrot")["target_epoch"]
    assert pending["member_ids"] != row["active_ids"]


def test_golf_cidr_reuse(report):
    """Golf reuses retired AllowedIPs 10.70.1.0/24 on m-g3 at epoch three."""
    row = next(r for r in report["nodes"] if r["node_id"] == "golf")
    assert row == expected_node_row("golf")
    table = load_epoch_table("golf")
    prior_cidrs = set()
    for erow in table["epochs"]:
        if erow["epoch"] < 3:
            for m in erow["members"]:
                prior_cidrs.update(m["allowed_ips"])
    target_cidrs = set()
    for erow in table["epochs"]:
        if erow["epoch"] == 3:
            for m in erow["members"]:
                target_cidrs.update(m["allowed_ips"])
    assert prior_cidrs & target_cidrs
    assert "m-g3" in row["active_ids"]
    assert "m-g4" in row["active_ids"]


def test_hotel_carry_forward(report):
    """Hotel keeps carry-forward peer m-h2 while retiring m-h3."""
    row = next(r for r in report["nodes"] if r["node_id"] == "hotel")
    assert row == expected_node_row("hotel")
    assert row["active_ids"] == ["m-h2", "m-h4"]
    table = load_epoch_table("hotel")
    ep2 = next(r["members"] for r in table["epochs"] if r["epoch"] == 2)
    ep3 = next(r["members"] for r in table["epochs"] if r["epoch"] == 3)
    assert {{m["id"] for m in ep2}} & {{m["id"] for m in ep3}} == {{"m-h2"}}


def test_carry_forward_not_treated_as_retired(report):
    """Peers present in both prior and target epochs remain on the wire."""
    for node_id in load_bundle_index():
        target = set(target_member_ids(node_id))
        table = load_epoch_table(node_id)
        manifest = load_manifest(node_id)
        prior = set()
        for erow in table["epochs"]:
            if erow["epoch"] < manifest["target_epoch"]:
                prior.update(m["id"] for m in erow["members"])
        carry = prior & target
        if not carry:
            continue
        row = next(r for r in report["nodes"] if r["node_id"] == node_id)
        assert carry.issubset(set(row["active_ids"]))


def test_policy_cutover_knobs_intact():
    """Cutover policy knobs remain the lab defaults."""
    text = (OPT / "data" / "policy.toml").read_text(encoding="utf-8")
    assert 'epoch_authority = "manifest"' in text
    assert 'roster_source = "epoch_table"' in text
    assert 'staging_mode = "replace"' in text
    assert "allow_cidr_reuse = true" in text


def test_drifts_empty(report):
    """No stale members remain after reconcile."""
    assert report["drifts"] == []


def test_full_report(report):
    """Aggregate report matches scenario-derived expectations."""
    assert report == expected_report()


def test_scenario_fixtures_intact():
    """Bundled scenario manifests match the lab bundle index."""
    index = load_bundle_index()
    assert set(index) == set(index.keys())
    for node_id, meta in index.items():
        manifest = load_manifest(node_id)
        assert manifest["node_id"] == node_id
        assert manifest["target_epoch"] == meta["target_epoch"]


def test_pending_files_unmodified():
    """Verifier does not rewrite automation queue fixtures."""
    for node_id in load_bundle_index():
        pending_path = SCENARIO_ROOT / node_id / "pending.json"
        before = pending_path.read_text(encoding="utf-8")
        run_tool()
        after = pending_path.read_text(encoding="utf-8")
        assert before == after


def test_determinism():
    """Back-to-back runs produce identical JSON."""
    first = run_tool()
    second = run_tool()
    assert first == second
'''
    w("tests/test_outputs.py", body)


def write_solve() -> None:
    w(
        "solution/solve.sh",
        """
        #!/bin/bash
        set -euo pipefail
        cd {TASK_ROOT}

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
        bin/reconcile --policy data/policy.toml --scenarios data/scenarios --out {OUTPUT_ROOT}
        """,
    )


def write_dockerfile() -> None:
    w(
        "environment/Dockerfile",
        """
        # syntax=docker/dockerfile:1

        FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac AS builder

        WORKDIR /build
        COPY go.mod ./
        RUN go mod download
        COPY cmd/ ./cmd/
        COPY internal/ ./internal/
        RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/reconcile ./cmd/reconcile

        FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac

        LABEL org.opencontainers.image.source="terminal-bench-3"
        LABEL org.opencontainers.image.version="1.0.0"
        LABEL org.opencontainers.image.licenses="MIT"

        # Agent runtime requires tmux and asciinema before any other setup.
        RUN apt-get update \\
            && apt-get install -y --no-install-recommends \\
                tmux=3.3a-3 \\
                asciinema=2.2.0-1 \\
            && rm -rf /var/lib/apt/lists/*

        ENV TERM=xterm-256color

        RUN tmux -V && asciinema --version

        RUN apt-get update \\
            && apt-get install -y --no-install-recommends \\
                bash \\
                ca-certificates \\
                libutempter0 \\
                procps \\
                python3 \\
                python3-pip \\
            && rm -rf /var/lib/apt/lists/*

        RUN pip3 install --no-cache-dir --break-system-packages \\
            pytest==8.4.1 \\
            pytest-json-ctrf==0.3.5

        ENV GOPATH=/go \\
            GOCACHE=/tmp/go-cache
        RUN mkdir -p /go /tmp/go-cache

        COPY --from=builder --chmod=755 /out/reconcile /opt/wghandoff/bin/reconcile
        COPY go.mod /opt/wghandoff/
        COPY cmd/ /opt/wghandoff/cmd/
        COPY internal/ /opt/wghandoff/internal/
        COPY scripts/ /opt/wghandoff/scripts/
        COPY data/ /opt/wghandoff/data/
        COPY config/ /opt/wghandoff/config/
        COPY docs/ /opt/wghandoff/docs/

        RUN chmod +x /opt/wghandoff/scripts/*.sh \\
            && cd /opt/wghandoff && go mod download

        RUN tmux -V \\
            && asciinema --version \\
            && tmux new-session -d -s _smoke \\
            && tmux has-session -t _smoke \\
            && tmux send-keys -t _smoke 'echo tmux_ok' Enter \\
            && tmux capture-pane -t _smoke -p | grep -q tmux_ok \\
            && tmux kill-session -t _smoke

        WORKDIR /opt/wghandoff
        ENV PATH="/opt/wghandoff/bin:${PATH}"
        """,
    )
    w(
        "environment/.dockerignore",
        """
        .git
        .gitignore
        **/__pycache__/
        **/*.pyc
        **/.pytest_cache/
        **/.mypy_cache/
        **/.ruff_cache/
        **/node_modules/
        **/target/
        **/dist/
        **/build/
        **/.venv/
        **/venv/
        .env
        *.log
        solution/
        tests/
        """,
    )


def write_go_sum() -> None:
    pass


def main() -> None:
    import shutil

    if TASK.exists():
        shutil.rmtree(TASK)
    write_scenarios()
    write_go_sources()
    write_dockerfile()
    write_go_sum()
    write_task_meta()
    write_tests()
    write_solve()
    for sh in (ENV / "scripts").glob("*.sh"):
        sh.chmod(0o755)
    (TASK / "solution" / "solve.sh").chmod(0o755)
    (TASK / "tests" / "test.sh").chmod(0o755)
    print(f"Wrote {TASK}")
    print("Report GT nodes:", len(REPORT_GT["nodes"]))


if __name__ == "__main__":
    main()
