# package-registry-yank-window

## Authoring Brief

Package index yank-window reconciliation across Rust `indexctl` and Go `advscan`.
Half-open yank intervals, revoke ledger, transitive required-dep installability,
optional-dep exemption, live-only advisories, and severity floor `high`.
Not the three-authority epoch-lag pattern.

### Failure topology
1. Closed upper bound keeps `until == head` windows active
2. Revoke ledger ignored for open-ended yanks
3. Installability checks only direct edges and treats optional deps as required
4. Advisory path ignores half-open/revokes/severity floor
5. Operator table defaults: closed bounds, honor_revokes=false, adv_live_only=false, adv_floor=low

### symbol_table
- config/l7/k9.toml :: bound_mode, honor_revokes, adv_live_only, adv_floor
- rsx/core/src/q_slot.rs :: yank_holds / active_yank_set
- rsx/core/src/k_net.rs :: installable_rows (transitive + optional)
- rsx/core/src/lib.rs :: advisory severity floor filter
- scan/internal/m4/live.go :: AdvisoryDigest

### flipping_point_contract
- bound_mode: exclusive_upper_bound_clears_yank, open_ended_yank_remains_active
- honor_revokes: revoke_clears_open_ended_yank
- transitive/optional: transitive_yank_blocks_indirect_consumer, optional_yanked_dep_does_not_block
- adv_floor/live: advisory_severity_floor_drops_live_low, advscan_digest_alignment

### Anti-cheat notes
- No agent-visible reference oracle script; expected digests live under tests/
- Verifier re-runs `/app/bin/indexctl report` rather than trusting a pre-written JSON alone
- Input ledgers cover crates, yanks, and advisories
