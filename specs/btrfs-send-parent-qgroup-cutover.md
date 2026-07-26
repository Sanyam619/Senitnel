### Decision
GO — Attempt 1. Sysadmin cutover on live `/etc/btrfs` + `/var/lib/btrfs` with correct prebuilt Rust `bops`; broken Go/C ops helpers for journal fold, preference depth, generation gate, hold rematerialize, and hardlink attach. Fair tip-map rewrite and dual-residency outcomes stated as scenarios.

### Metadata
- version: 2
- Task name: btrfs-send-parent-qgroup-cutover
- Title: Btrfs Send Parent Cutover
- Category: system-administration
- Languages: ["rust", "go", "c"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["btrfs-send", "qgroup", "ops-journal", "leases", "parent-uuid"]
- Milestones: 0

## Authoring Brief

### Public contract
After storage cutover, restore live btrfs admin state so roster lanes emit correct send streams under `/output/lanes/<name>/stream.bin` and `/output/send-report.json` (seal_gen, lanes[{name,parent_uuid,snap_uuid,origin_kind,order_index}]). origin_kind is `incr` or `base` under equality-inclusive preference. Only roster lanes appear. Rewrite `/var/lib/btrfs/meta/parents.toml` from the sealed journal. Clear leases and host markers; attach via same-inode hardlink to sealed shelves. Entrypoint `/app/ops/run_cutover.sh`; prebuilt `/app/bin/bops`; surface `/app/bin/healthb` may green incorrectly.

### Failure topology
Crash left send parents on decoy UUIDs, qgroup mode wrong via drop-in fold, leases beyond seal gen, copy-only holds leaving host markers, and decoy volume copies instead of hardlink identity. Surface health is green while streams and quotas disagree. Helpers and binary interact: partial helper fixes leave tip-map, inode, or lease invariants failing distant tests.

### Environment shape
- `/etc/btrfs/` seal, lane roster, pref.d drop-ins
- `/var/lib/btrfs/` journal WAL, origins/snaps/decoys, volumes, meta tip-map, attach points
- `/var/run/btrfs/` leases
- `/app/ops/` entrypoint + Go/C helpers
- `/app/bin/` correct Rust bops + healthb
- `/app/docs/` layout notes (no knob checklist)

### Required artifacts
instruction.md, task.toml, output_contract.toml, environment/Dockerfile + .dockerignore, Rust src for bops/healthb, Go helpers (knit_p/fold_q/slot_w), C helpers (hold_c/link_v), fixtures, docs, solution/solve.sh, tests/test.sh + test_outputs.py. ≥20 environment files.

### Test plan
1. Seal-cap parent — alpha stream follows sealed parent, not beyond-seal bogus
2. Below-floor base — gamma/beta reject decoy and below-floor incr tip
3. Equality boundary — delta at epoch==floor is incr under equality-inclusive
4. Report fields — parent_uuid, snap_uuid, origin_kind, order_index match sealed sequence
5. Origins immutable + no lease markers
6. Idempotent second cutover + clean leases
7. Concurrent cutover clean leases + matching streams
8. parents.toml tip-map rewrite (stale crash tips gone; roster-only)
9. healthb OK does not excuse wrong incr payloads
10. Off-roster omega absent from output, report, tip-map
11. seal_gen matches active seal
12. Hardlink inode identity vs sealed shelf
13. Host markers absent under volumes/*/host/ after cutover

### Drafting guardrails
Symptoms-only instruction; document tip-map rewrite, dual residency, hardlink, equality-inclusive as outcomes not recipes. Opaque helper names. No answer-shaped docs. No make/cargo recipe as the task. Verifier-owned EXPECTED rebuilt from seal+roster+WAL. Tags ops-flavored.

### Triviality Ledger
- Three polarity stub rewrite alone fails: tip-map rewrite + hardlink + host-clear + seal-cap roster filter are coupled; fixing only preference mode still fails tip-map and inode tests.
- Hand-writing report JSON fails: tests re-invoke run_cutover.sh and assert live tip-map, inodes, and stream bytes from shelves.
- Ignoring healthb still required: payload and tip-map tests independent of surface OK.
- Naive tip-map edit undone unless knit_p rewrites parents.toml each pass from sealed journal.
- Copy-only hold leaves host markers that dual-residency test fails.

### Per-gate Pitfall Inventory
- RC1: oracle rewrites helper bodies with substantive fold/attach logic, not delete BUG flags.
- RC2: opaque test/helper names (no broken_/fix_me_).
- RC3: tests assert stream bytes, tip-map, inodes, seals — not schema alone.
- RC4/RC5: EXPECTED derived in tests from WAL+seal+roster; no golden under environment/.
- RC6: symptoms-only; fair outcomes stated without naming fix files.
- RC7: solve.sh ≥30 LOC substantive helper replacements.
- GX9/GX10: no per-lane answer recital; no polarity contradiction.
- Static: allow_internet=false; pinned deps; PYTHONSAFEPATH=1; .dockerignore; no COPY hidden paths.

### Initial Draft Commitments
- tasks/btrfs-send-parent-qgroup-cutover/instruction.md
- tasks/btrfs-send-parent-qgroup-cutover/task.toml
- tasks/btrfs-send-parent-qgroup-cutover/output_contract.toml
- tasks/btrfs-send-parent-qgroup-cutover/solution/solve.sh
- tasks/btrfs-send-parent-qgroup-cutover/tests/test.sh
- tasks/btrfs-send-parent-qgroup-cutover/tests/test_outputs.py
- tasks/btrfs-send-parent-qgroup-cutover/environment/Dockerfile
- tasks/btrfs-send-parent-qgroup-cutover/environment/.dockerignore
- tasks/btrfs-send-parent-qgroup-cutover/environment/Cargo.toml
- tasks/btrfs-send-parent-qgroup-cutover/environment/Cargo.lock
- tasks/btrfs-send-parent-qgroup-cutover/environment/src/bops.rs
- tasks/btrfs-send-parent-qgroup-cutover/environment/src/healthb.rs
- tasks/btrfs-send-parent-qgroup-cutover/environment/ops/run_cutover.sh
- tasks/btrfs-send-parent-qgroup-cutover/environment/ops/go/go.mod
- tasks/btrfs-send-parent-qgroup-cutover/environment/ops/go/knit_p/main.go
- tasks/btrfs-send-parent-qgroup-cutover/environment/ops/go/fold_q/main.go
- tasks/btrfs-send-parent-qgroup-cutover/environment/ops/go/slot_w/main.go
- tasks/btrfs-send-parent-qgroup-cutover/environment/ops/c/hold_c.c
- tasks/btrfs-send-parent-qgroup-cutover/environment/ops/c/link_v.c
- tasks/btrfs-send-parent-qgroup-cutover/environment/docs/layout.md
- tasks/btrfs-send-parent-qgroup-cutover/environment/docs/operator-notes.md
- tasks/btrfs-send-parent-qgroup-cutover/environment/etc/btrfs/pool.seal
- tasks/btrfs-send-parent-qgroup-cutover/environment/etc/btrfs/lane.roster
- tasks/btrfs-send-parent-qgroup-cutover/environment/etc/btrfs/pref.d/10-core.conf
- tasks/btrfs-send-parent-qgroup-cutover/environment/etc/btrfs/pref.d/40-lab.conf
- tasks/btrfs-send-parent-qgroup-cutover/environment/etc/btrfs/pref.d/90-local.conf
- tasks/btrfs-send-parent-qgroup-cutover/environment/data/btrfs/journal/send.wal
- tasks/btrfs-send-parent-qgroup-cutover/environment/data/btrfs/meta/parents.toml
- tasks/btrfs-send-parent-qgroup-cutover/environment/data/build_fixtures.py
- tasks/btrfs-send-parent-qgroup-cutover/environment/packaging/README.md
- tasks/btrfs-send-parent-qgroup-cutover/environment/config/site_notes.conf
- plus origin/snap/decoy/volume payload binaries generated by build_fixtures.py

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table
```
- path: ops/go/knit_p/main.go
  symbol: main
  kind: function
  signature: func main()
  purpose: fold sealed journal into runtime.tsv and parents.toml
- path: ops/go/fold_q/main.go
  symbol: main
  kind: function
  signature: func main()
  purpose: fold pref.d drop-ins and arm qgroup mode
- path: ops/go/slot_w/main.go
  symbol: main
  kind: function
  signature: func main()
  purpose: arm seal generation gate file for leases
- path: ops/c/hold_c.c
  symbol: main
  kind: function
  signature: int main(int argc, char **argv)
  purpose: rematerialize holds and clear lease/host markers
- path: ops/c/link_v.c
  symbol: main
  kind: function
  signature: int main(int argc, char **argv)
  purpose: attach sealed volume via same-inode hardlink
```

#### flipping_point_contract
```
locations:
  - id: A
    path: ops/go/knit_p/main.go
    controls_tests: [test_k3_zircon, test_w9_quartz, test_n5_beryl, test_q7_topaz]
  - id: B
    path: ops/go/fold_q/main.go
    controls_tests: [test_p2_garnet, test_m8_obsidian, test_y3_coral, test_x2_flint]
  - id: C
    path: ops/c/hold_c.c
    controls_tests: [test_r1_onyx, test_t6_amber, test_v4_jade, test_h2_coral]
  - id: D
    path: ops/c/link_v.c
    controls_tests: [test_i8_flint]
  - id: E
    path: ops/go/slot_w/main.go
    controls_tests: [test_s4_jade]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest
```
- path: ops/go/aux_scan/main.go
  kind: helper
  rhymes_with: knit_p
  non_fix_purpose: optional journal line counter used by packaging notes only
- path: ops/c/stat_z.c
  kind: helper
  rhymes_with: link_v
  non_fix_purpose: prints inode of a path for operator inspection
- path: docs/operator-notes.md
  kind: config-reader
  rhymes_with: fold_q
  non_fix_purpose: describes normal layout without preference formula
```

#### code_forbidden_tokens
```
code_forbidden_tokens: [storage, cutover, incremental, btrfs, send, parent, parents, snapshot, lineage, lease, leases, qgroup, lane, lanes, stream, report, seal, roster, preference, drop-in, inherit, epoch, floor, origin, shelf, host, marker, volume, attach, inode, hardlink, journal, receive, quota, healthb, bops]
```
