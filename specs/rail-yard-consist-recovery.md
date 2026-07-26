# rail-yard-consist-recovery

## Authoring Brief

Symptoms-only instruction describing diverged train consist assignments after partial yard replay. Agent may edit `/app/config/l7/`, Go movement audit lane, and Rust consist ledger. Tests derive expected track maps and audit digests from `/app/data/events/` fixtures and movement head. Output `/output/consist-report.json` with `replay_seq`, `tracks`, and `audit_digest`. `lane probe` must match `replay_seq`.

### Failure topology
Three authorities lag after promotion: Go ResolveSeq scans tier_b (seq 3) while tier_c holds seq 6; Rust seq_cut prefers last_replay_seq; operator replay_watermark pins sequence 3. C103 on T1 absent until all three align.

### Triviality Ledger
- Config-only without lane tier fix leaves seq at 3 — blocked by lane_probe_alignment.
- Lane-only without Rust seq_cut leaves stale tracks — blocked by promoted_car_on_t1.
- Rust-only without config watermark keeps seq_cut capped — blocked by config_replay_watermark_cleared.

### Per-gate Pitfall Inventory
- RC1: oracle touches config, Go seq.go/probe.go, Rust seq_cut — multi-file.
- RC3/GX3: decoy k3/ScanTierA rhymes with ResolveSeq but unwired.
- CR7: code_forbidden_tokens on fix-path symbols.

### Construction manifest

#### symbol_table
- path: lane/internal/m7/seq.go
  symbol: pickTier
  kind: function
- path: lane/internal/m7/probe.go
  symbol: WriteProbe
  kind: function
- path: ledger/core/src/lib.rs
  symbol: seq_cut
  kind: function
- path: config/l7/k9.toml
  symbol: replay_watermark
  kind: constant

#### flipping_point_contract
locations:
  - id: A
    path: lane/internal/m7/seq.go
    controls_tests: [test_lane_probe_alignment, test_replay_seq_matches_movement_head]
  - id: B
    path: ledger/core/src/lib.rs
    controls_tests: [test_promoted_car_on_t1, test_audit_digest_matches_fixture_probe]
  - id: C
    path: config/l7/k9.toml
    controls_tests: [test_config_replay_watermark_cleared, test_runtime_active_matches_head]
no_single_location_flips_majority: true

#### code_forbidden_tokens
code_forbidden_tokens: [rail, yard, consist, train, movement, audit, replay, track, car, ledger, reconcile, probe, window, fixture, promote, sequence, head, digest, visible, operator, lane, yardctl, report, watermark, runtime, active, last, promoted, partial, diverged, assignment, aggregate, checks, fail, expectations, serving, started, landed, promotion, disk, still, hand-edit, files, under, paths, bin, may, code, changes, do, not, the, and, for, each, that, those, with, via, out, from, see, but, an, at, three, two, one, four, five, six, seven, eight, nine, ten]
