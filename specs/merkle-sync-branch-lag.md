# merkle-sync-branch-lag

## Authoring Brief

Symptoms-only instruction describing stale incremental sync digests after branch promotion. Agent may edit `/app/config/l7/`, Go lane checkpoint reader, and Rust tree builder. Tests derive expected leaf and root digests from `/app/data/leaves/` fixtures and journal head. Output `/output/sync-report.json` with `branch_gen`, `root_digest`, and per-leaf digests. `lane head` must match `branch_gen`.

### Failure topology
Three authorities lag after promotion: Go ResolveHead scans tier_b (gen 2) while tier_c holds gen 3; Rust branch_cut prefers last_sync_gen; operator branch_cap pins generation 2. Delta leaf (since=3) absent until all three align.

### Triviality Ledger
- Config-only without lane tier fix leaves head at 2 — blocked by lane_head_alignment.
- Lane-only without Rust branch_cut leaves stale tree — blocked by promoted_leaf_present.
- Rust-only without config cap keeps branch_cut capped — blocked by config_branch_cap_cleared.

### Per-gate Pitfall Inventory
- RC1: oracle touches config, Go head.go/summary.go, Rust branch_cut — multi-file.
- RC3/GX3: decoy k3/ScanTierA rhymes with ResolveHead but unwired.
- CR7: code_forbidden_tokens on fix-path symbols.

### Construction manifest

#### symbol_table
- path: lane/internal/m7/head.go
  symbol: pickTier
  kind: function
- path: lane/internal/m7/summary.go
  symbol: WriteSummary
  kind: function
- path: tree/core/src/lib.rs
  symbol: branch_cut
  kind: function
- path: config/l7/k9.toml
  symbol: branch_cap
  kind: constant

#### flipping_point_contract
locations:
  - id: A
    path: lane/internal/m7/head.go
    controls_tests: [test_lane_head_alignment, test_branch_gen_matches_journal_head]
  - id: B
    path: tree/core/src/lib.rs
    controls_tests: [test_promoted_leaf_present, test_root_digest_matches_fixture_tree]
  - id: C
    path: config/l7/k9.toml
    controls_tests: [test_config_branch_cap_cleared, test_runtime_active_matches_head]
no_single_location_flips_majority: true

#### code_forbidden_tokens
code_forbidden_tokens: [merkle, sync, branch, lag, stale, leaf, checkpoint, digest, incremental, promote, generation, reconcile, tree, reader, builder, fixture, journal, tier, head, root, visible, canonical, operator, lane, syncctl, report, cap, runtime, active, last, promoted, delta, gamma, alpha, fixture-derived, cross-language, bind, scan, emit, workflow, recovery, peers, trust, aggregate, payload, since, map, hex, integer, object, write, rebuild, edit, tables, sources, data, config, output, app, must, agree, prints, same, matches, on-disk, after, again, when, never, appears, reflects, older, checks, fail, expectations, serving, started, landed, promotion, disk, still, hand-edit, files, under, paths, bin, may, code, changes, do, not, the, and, for, each, that, those, with, via, out, from, see, but, an, at, three, two, one, four, five, six, seven, eight, nine, ten]
