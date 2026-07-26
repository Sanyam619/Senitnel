# wasm-module-linker-skew

## Authoring Brief

Symptoms-only instruction for WASM module graph skew after partial compile. Agent edits `/app/config/l7/`, Go gate epoch reader, and Rust link epoch cut. Tests derive expected digests from `/app/data/modules/` via graph_lab. Output `/output/link-report.json`. `gatectl epoch` must match report `epoch`.

### Failure topology
Three authorities lag after promotion: Go ResolveEpoch scans tier_b (epoch 2); Rust epoch_cut prefers last_link_epoch; operator link_epoch_cap pins epoch 2. Filter module (since=3) absent until all three align.

### symbol_table
- gate/internal/m4/epoch.go :: ResolveEpoch
- wasm/core/src/lib.rs :: epoch_cut
- config/l7/k9.toml :: link_epoch_cap
- config/l7/m2.toml :: scan_tier

### flipping_point_contract
- Go gate fix: gatectl_epoch_alignment, epoch_matches_manifest_head
- Rust link table fix: filter_module_present, graph_digest_matches_fixture
- Config cap fix: config_link_epoch_cap_cleared
