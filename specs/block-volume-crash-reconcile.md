### Decision
GO — Attempt 1. Idea validated against existing corpus; maps to pre-built `block-volume-crash-reconcile` generator. Symptoms-only instruction, KVFS on-disk format with multi-scenario golden verification, 27 environment files.

### Metadata
- version: 2
- Task name: block-volume-crash-reconcile
- Title: Block Volume Crash Reconcile
- Category: system-administration
- Languages: ["c"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["filesystem", "crash-recovery", "block-device", "c", "data-integrity"]
- Milestones: 0

## Authoring Brief

### Public contract
Six raw KVFS block-device images (`shard_a`–`shard_f`) under `/opt/kvfs/data/scenarios/` after unclean shutdown. Agent must reconcile each image and emit `/output/recovered_state.json` (per-shard `chosen_superblock`, `files` path→SHA-256 hex, `bitmap_hex`) plus six rebuilt full images under `/output/rebuilt_shard_*.img`. C toolchain at `/opt/kvfs`; read-only `volpeek` inspector (must not be rebuilt); format and recovery contract in `vol_format.md`. Bash only for builds and ops hooks.

### Failure topology
Symptoms cluster around stale inode payloads, bitmap double-allocation, and disagreeing redundant volume headers. Recovery requires picking the authoritative header (epoch + durable generation + CRC validity), replaying only sealed redo transactions in order, and honoring block-forget records that suppress replay of blocks later reused—naive “replay every patch” corrupts `shard_b`. Unsealed transactions must not apply. Bitmap must be recomputed from reconciled inode direct blocks plus metadata regions.

### Environment shape
`/opt/kvfs/include` — packed structs; `/opt/kvfs/lib` — volume open, header pick (stub), journal scan (partial), inode walk, CRC; `/opt/kvfs/tools/volpeek` read-only inspector; `/opt/kvfs/docs/vol_format.md` on-disk record layout; `/opt/kvfs/data/scenarios/*.img` crash copies; `/opt/kvfs/config`, `/opt/kvfs/ops`, `/opt/kvfs/packaging` supporting material.

### Required artifacts
`instruction.md`, `task.toml`, `output_contract.toml`, `environment/` (Dockerfile, .dockerignore, Makefile, headers, lib, tools, docs, data, config, ops), `solution/solve.sh`, `tests/{test.sh, test_outputs.py}`.

### Test plan
- `test_recovered_state_exists` — JSON and four rebuilt images present
- `test_shard_a_unsealed_tx_ignored` — partial tx does not change `/notes.txt` digest
- `test_shard_b_forget_suppression` — ALPHA_V2 not resurrected after block reuse
- `test_shard_c_superblock_epoch_tiebreak` — correct header when epochs diverge
- `test_shard_d_bitmap_rebuilt` — stale bitmap corrected after replay
- `test_rebuilt_images_match_golden_layout` — inode table and payloads byte-consistent
- `test_volpeek_unchanged` — scenario inputs not modified

### Drafting guardrails
Instruction stays symptoms-only: no “revoke”, “ordered mode”, “journal replay”. Code symbols use opaque names (`reconcile_b_image`, `m3_apply`, `resolve_c_pick_header`). Tests derive golden via independent Python reconcile, not env fixtures.

### Triviality Ledger
- Naive replay-all-patches passes `shard_a`/`shard_c` but fails `shard_b` because BLK_FORGET suppression is required after sealed reuse.
- Picking header by `durable_tx` alone fails `shard_c` where epoch ordering breaks ties.
- Copying on-disk bitmap without replay fails `shard_d` double-allocation scenario.

### Per-gate Pitfall Inventory
- RC6: instruction names SHA-256 for output contract only; no redo tag semantics in prose.
- RC7: oracle ~250 LOC substantive C in `m3_apply.c` + `reconcile.c`.
- GX9: instruction does not recite per-shard digests.
- GX10: no polarity contradictions on binary fields.
- Static: `allow_internet = false`, 27 env files, `.dockerignore` present.

### Initial Draft Commitments
- `tasks/block-volume-crash-reconcile/instruction.md`
- `tasks/block-volume-crash-reconcile/task.toml`
- `tasks/block-volume-crash-reconcile/output_contract.toml`
- `tasks/block-volume-crash-reconcile/environment/Dockerfile`
- `tasks/block-volume-crash-reconcile/environment/.dockerignore`
- `tasks/block-volume-crash-reconcile/environment/Makefile`
- `tasks/block-volume-crash-reconcile/environment/include/kvfs_layout.h`
- `tasks/block-volume-crash-reconcile/environment/include/kvfs_api.h`
- `tasks/block-volume-crash-reconcile/environment/include/kvfs_crc.h`
- `tasks/block-volume-crash-reconcile/environment/lib/kvfs_internal.h`
- `tasks/block-volume-crash-reconcile/environment/lib/p7_sb.c`
- `tasks/block-volume-crash-reconcile/environment/lib/k9_scan.c`
- `tasks/block-volume-crash-reconcile/environment/lib/m3_apply.c`
- `tasks/block-volume-crash-reconcile/environment/lib/r2_inode.c`
- `tasks/block-volume-crash-reconcile/environment/lib/u8_crc.c`
- `tasks/block-volume-crash-reconcile/environment/tools/volpeek.c`
- `tasks/block-volume-crash-reconcile/environment/tools/reconcile.c`
- `tasks/block-volume-crash-reconcile/environment/docs/vol_format.md`
- `tasks/block-volume-crash-reconcile/environment/docs/glossary.txt`
- `tasks/block-volume-crash-reconcile/environment/data/scenarios/shard_{a,b,c,d}.img`
- `tasks/block-volume-crash-reconcile/environment/data/README.txt`
- `tasks/block-volume-crash-reconcile/environment/config/build_flags.mk`
- `tasks/block-volume-crash-reconcile/environment/config/paths.mk`
- `tasks/block-volume-crash-reconcile/environment/ops/check_image.sh`
- `tasks/block-volume-crash-reconcile/environment/ops/mount_notes.txt`
- `tasks/block-volume-crash-reconcile/environment/packaging/version.txt`
- `tasks/block-volume-crash-reconcile/tests/test.sh`
- `tasks/block-volume-crash-reconcile/tests/test_outputs.py`
- `tasks/block-volume-crash-reconcile/solution/solve.sh`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table
- path: environment/lib/m3_apply.c
  symbol: reconcile_b_image
  kind: function
  signature: int reconcile_b_image(const uint8_t *img, size_t len, uint8_t *work, uint32_t *chosen_super, char *bitmap_hex, size_t bitmap_hex_cap)
  purpose: replay sealed redo records with forget suppression and rebuild bitmap
- path: environment/lib/p7_sb.c
  symbol: resolve_c_pick_header
  kind: function
  signature: int resolve_c_pick_header(kvfs_volume *vol, uint32_t *chosen_blk)
  purpose: select redundant volume header candidate (stub in env; oracle replaces)
- path: environment/tools/reconcile.c
  symbol: main
  kind: function
  signature: int main(void)
  purpose: drive per-shard reconcile and emit JSON plus rebuilt images

#### flipping_point_contract
locations:
  - id: A
    path: environment/lib/m3_apply.c
    controls_tests: [test_shard_b_forget_suppression, test_shard_d_bitmap_rebuilt]
  - id: B
    path: environment/lib/p7_sb.c
    controls_tests: [test_shard_c_superblock_epoch_tiebreak]
  - id: C
    path: environment/tools/reconcile.c
    controls_tests: [test_recovered_state_exists, test_rebuilt_images_match_golden_layout]
no_single_location_flips_majority: true
concentration_cap: 0.5

#### decoy_manifest
- path: environment/lib/k9_scan.c
  kind: module
  rhymes_with: reconcile_b_image
  non_fix_purpose: counts sealed TX_SEAL records only; does not apply patches
- path: environment/lib/r2_inode.c
  kind: module
  rhymes_with: reconcile_b_image
  non_fix_purpose: walks live inode table without redo replay

#### code_forbidden_tokens
code_forbidden_tokens: [operations, storage, node, power, mount, regular, files, payload, free-block, map, redundant, volume, headers, byte, layout, inspector, inodes, circular, redo, area, basename, suffix, integer, object, mapping, absolute, paths, lowercase, hex, digests, contiguous, full, raw, length, inputs, table, allocation, scenarios, inspector, read-only]
