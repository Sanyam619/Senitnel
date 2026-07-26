### Decision
GO — Attempt 1. Dual-language distributed-log recovery with divergent post-crash generations; Go replay lane must align with Rust manifest tier and ctl workflow.

### Metadata
- version: 2
- Task name: raft-snapshot-fork-reconcile
- Title: Snapshot fork reconcile
- Category: system-administration
- Languages: ["go", "rust"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["distributed-log", "operational-recovery", "manifest", "wal", "go-rust", "replay"]
- Milestones: 0

## Authoring Brief

### Public contract
Symptoms-only instruction describing inconsistent events queries after a crash left competing snapshot generations. Agent may edit `/app/config/l7/` operator tables and `/app/lane/` Go sources; Rust store is read-only. Recovery uses ctl roll/barrier/rebuild workflow. Output `/output/fork-report.json` with `restored_generation`, per-namespace `visible_segments`, and `sidecar_digest`. Deterministic replay probes via ctl query at timestamp 550.

### Failure topology
Two authorities disagree after crash: Rust manifest tier journals record a pre-fork anchor while a fork head generation remains on disk; Go replay lane selects the fork head from the wrong journal tier. Operator tables ship with unsafe phase order, wrong anchor pin, and disabled barrier cutoff. Query path uses stale sidecar binding until roll/barrier/rebuild completes. Metrics namespace stays stable as control.

### Environment shape
`/app/store/` Rust workspace (ctl, manifest, wal, index, ops). `/app/lane/` Go replay module. `/app/data/` columns, sidecars, manifests, wal, runtime state. `/app/config/l7/` operator tables. `/app/ops/runbooks/` reference. `/app/bin/ctl` and `/app/bin/lane` binaries.

### Required artifacts
instruction.md, task.toml, output_contract.toml, environment/Dockerfile, environment/.dockerignore, Go lane module, Rust store copy, fixtures, solution/solve.sh, tests/test.sh, tests/test_outputs.py.

### Test plan
- Point/range/aggregate ctl probes against fixture columns
- Tombstone absence at query window
- fork-report schema and generation bounds
- Runtime chain alignment with manifest anchor
- Operator table phase order and cutoff fields
- Sidecar digest match on disk
- Metrics namespace stability
- Lane head matches runtime active generation
- Lane report agrees with ctl report fields

### Drafting guardrails
Instruction uses snapshot/fork/replay/manifest tier vocabulary; fix-path Go symbols stay opaque (m7, k3, splitMark). No Rust edits in oracle. Tests must not embed instruction nouns as substrings in function names.

### Triviality Ledger
- Setting only k9.toml tier_c without fixing lane tier picker leaves fork-head selection — blocked by lane/runtime generation test.
- Running rebuild before barrier leaves tombstone keys visible — blocked by marker absence probe.
- Copying ctl report JSON without lane emit — blocked by lane head pre-report check in oracle and lane generation test.

### Per-gate Pitfall Inventory
- RC1: oracle touches config tables, Go branch.go, and workflow phases — multi-file.
- RC3/GX3: decoy k3/anchor helper and index rebuild_fast module provide non-fix rhymes.
- CR7: code_forbidden_tokens lists instruction nouns; grep_resistance on Go/Rust fix frontier.
- GX10: concentration split across config, Go m7, and ctl workflow tests.

### Initial Draft Commitments
- instruction.md
- task.toml
- output_contract.toml
- solution/solve.sh
- tests/test.sh
- tests/test_outputs.py
- environment/Dockerfile
- environment/.dockerignore
- environment/lane/go.mod
- environment/lane/cmd/lane/main.go
- environment/lane/internal/m7/branch.go
- environment/lane/internal/m7/summary.go
- environment/lane/internal/k3/anchor.go
- environment/lane/pkg/frame/row.go
- environment/config/l7/k9.toml
- environment/config/l7/m2.toml
- environment/config/l7/p7.toml
- environment/config/l7/n3.toml
- environment/config/l7/r8.toml
- environment/data/state/runtime.json
- environment/data/manifests/tier_a.jsonl
- environment/data/manifests/tier_b.jsonl
- environment/data/manifests/tier_c.jsonl
- environment/data/wal/seg_001.bin
- environment/data/wal/seg_002.bin
- environment/data/columns/events_001.col
- environment/data/columns/events_002.col
- environment/data/columns/events_003.col
- environment/data/columns/events_merged.col
- environment/data/columns/metrics_010.col
- environment/data/columns/metrics_011.col
- environment/data/columns/metrics_merged.col
- environment/data/sidecars/events.idx
- environment/data/sidecars/metrics.idx
- environment/ops/runbooks/ctl_usage.md
- environment/store/** (full Rust workspace from reference)

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table
- path: lane/internal/m7/branch.go
  symbol: ResolveBranch
  kind: function
  signature: func ResolveBranch(manifestDir, ns string) (uint64, error)
  purpose: selects namespace generation for lane summary
- path: config/l7/k9.toml
  symbol: tier_c
  kind: constant
  signature: tier_c = <u64>
  purpose: roll anchor pin read by ctl roll phase
- path: config/l7/m2.toml
  symbol: seq_cutoff
  kind: constant
  signature: seq_cutoff = <u64>
  purpose: wal barrier cutoff for tombstone application
- path: config/l7/p7.toml
  symbol: phases
  kind: constant
  signature: phases = ["roll", "barrier", "rebuild"]
  purpose: ordered recovery workflow for ctl

#### flipping_point_contract
locations:
  - id: A
    path: lane/internal/m7/branch.go
    controls_tests: [test_lane_generation_matches_runtime, test_lane_report_matches_ctl_report]
  - id: B
    path: config/l7/k9.toml
    controls_tests: [test_recovery_config_phase_order, test_chain_order_invariant]
  - id: C
    path: config/l7/m2.toml
    controls_tests: [test_absent_marker_at_window, test_barrier_tombstone_runtime_state]
no_single_location_flips_majority: true
concentration_cap: 0.5

#### decoy_manifest
- path: lane/internal/k3/anchor.go
  kind: helper
  rhymes_with: ResolveBranch
  non_fix_purpose: standalone tier_b scanner not wired into stock lane emit path
- path: store/index/src/rebuild_fast.rs
  kind: module
  rhymes_with: rebuild
  non_fix_purpose: partial index patch helper unsafe after barrier

#### code_forbidden_tokens
code_forbidden_tokens: [snapshot, fork, replay, manifest, tier, generation, reconcile, raft, crash, divergent, align, engine, probe, recovery, barrier, roll, rebuild, wal, sidecar, events, metrics, operator, ctl, lane, report, digest, segments, tombstone, namespace, columns, journal, stripe, workflow, cutoff, anchor, ceiling, runtime, query, range, aggregate, point, key, payload, lexicographic, visible, restored, control-plane, shard, payloads, indexes, chains, subcommands, tables, sources, timestamps, status, positive, hex, string, integer, object, write, edit, rebuilds, subcommand, reference, runbooks, data, config, store, bin, output, app, must, after, same, order, matching, returns, scans, window, under, pattern, include, files, live, competing, untouched, disagree, says, should, what, left, two, with, from, through, applies, picks, admits, sorted, over, at, the, and, plus, each, not, exceed, reported, match, on-disk, for, that, namespace]
