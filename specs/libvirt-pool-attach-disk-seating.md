### Decision
GO — Attempt 1. Live libvirt pool/domain reconciliation with a sealed authority binary, four broken ops helpers, and a drift drop-in; hardness is coupled across durable-UUID resolution, pool activation path, key=value receipt gating, and preference-mode rematerialize.

### Metadata
- version: 2
- Task name: libvirt-pool-attach-disk-seating
- Title: Libvirt Pool Attach Seating
- Category: system-administration
- Languages: [bash]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: [libvirt, storage-pool, disk-attach, cutover-receipt, ops-journal, uuid-authority]
- Milestones: 0

## Authoring Brief

### Public contract
The operator entrypoint `/app/ops/run_pool_attach.sh` must reconcile live libvirt
storage-pool and domain state so it writes `/output/libvirt-attach.json`. The report
is JSON with `schema_tag` (string), `pools` (array of `{name, path, uuid, state}`),
`disks` (array of `{domain, target, source, pool, attached}`), and `attach_ok`
(boolean). Only roster pools/disks (declared under `/etc/libvirt/qemu/`) may appear.
A disk is `attached` only when its pool is active at the durable target path, the live
domain definition's disk source binds the durable pool UUID (not the surface-definition
decoy UUID), and a matching key=value cutover receipt exists under
`/var/lib/libvirt/ops/receipts/`. `attach_ok` is true only when every roster disk is
attached. `/usr/local/bin/virthealth` prints healthy regardless of real attach state.
Fixtures under `/app/data/pools/` stay byte-identical. Two consecutive entrypoint runs
must produce byte-identical `/output/libvirt-attach.json`.

### Failure topology
The post-crash live tree drifted from the durable authority under
`/var/lib/libvirt/ops/`. Four independent staging steps under `/app/ops/` are wrong:
(1) the seating resolver reads pool identity/path from the surface pool XML instead of
resolving the latest generation at-or-below the seal from the durable cutover journal;
(2) the pool activator seeds runtime state at the surface path / marks pools inactive;
(3) the receipt writer emits JSON instead of the key=value receipt the sealed authority
binary consumes; (4) the lock janitor leaves torn `.part`/`.lock` files. A live
selection drop-in under `/etc/libvirt/qemu/` sits at `authority=surface`, so the sealed
`/app/bin/virtattach` rematerializes every domain disk source back to the decoy UUID —
hand-editing the domain XML is undone on the next run, and deleting the drop-in leaves
the default surface preference (still wrong). The invariants are coupled: attach only
succeeds when pool state, source UUID, receipt, and preference mode all agree, so no
single edit passes the suite.

### Environment shape
- `environment/etc/libvirt/storage/` — surface pool definitions (decoy UUID/path) + seal.
- `environment/etc/libvirt/qemu/` — domain definitions, seating roster, selection drop-in dir.
- `environment/var/lib/libvirt/ops/` — durable cutover journal + receipts dir (empty).
- `environment/var/run/libvirt/` — lock/lease dir seeded with torn markers.
- `environment/app/data/pools/` — frozen volume fixtures.
- `environment/ops/` — entrypoint + four broken staging helpers + drop-in writer.
- `environment/cmd/ + internal/` — Go source for the sealed authority binary (build-time only; not shipped in the final image).
- `environment/docs/` — normal-layout operator notes (no repair recipe).

### Required artifacts
instruction.md (symptoms-only), task.toml, output_contract.toml, environment/ (Dockerfile,
.dockerignore, 20+ files: Go source, ops helpers, live etc/var surfaces, fixtures, docs),
solution/solve.sh, tests/test.sh, tests/test_outputs.py. Sealed Go binary built in a
builder stage and copied as an ELF; Go source not present in the final image.

### Test plan
1. durable UUID bound in report + live domain XML for pool-a disk (resolver + drop-in).
2. durable UUID for a second pool where the surface decoy differs (resolver + drop-in).
3. pool state active at durable path, not surface path (activator).
4. cutover receipts are key=value with durable UUID, not JSON (receipt writer).
5. attach_ok true only when all roster disks attached (coupled — global).
6. rematerialize: corrupt a live domain disk source, rerun, sealed binary restores durable UUID (drop-in + binary).
7. delete the selection drop-in, rerun -> attach fails / source reverts to decoy; then restore (drop-in gate).
8. torn `.part`/`.lock` markers cleaned after run (janitor).
9. two consecutive runs byte-identical report (determinism).
10. off-roster pool/domain never appears in report or as attached (scope).
11. frozen fixtures under /app/data/pools/ byte-identical (no-clobber).
12. virthealth prints OK yet a NOP report is absent/attach_ok false (surface bait).
Each test has multiple valid approaches for the staging logic; none is chain-dependent
beyond running the entrypoint, which every test does via a shared helper.

### Drafting guardrails
Instruction stays symptoms-only: no journal/seal algorithm, no key names, no file
locations of the broken helpers, no "durable vs surface" recipe. Helper filenames and
symbols are opaque (fold_g/seat_r/mark_c/tidy_v/pref_k). Docs describe normal layout and
name the drop-in `authority` key as ordinary config, never as the answer. Expected values
live in test code. The sealed binary carries the rematerialize/gate logic so the agent
cannot bypass staging by hand-editing XML.

### Triviality Ledger
- Naive "copy surface pool XML UUID into the plan" passes nothing: the sealed binary in
  durable mode writes the plan UUID, but the plan is wrong (decoy), so attach fails; the
  agent must resolve the durable journal generation at/below the seal.
- "Hand-edit the domain XML to the durable UUID" is undone every run by the sealed binary
  rematerializing from the plan/preference — forces fixing the resolver + drop-in, not the XML.
- "Delete the selection drop-in to stop rematerialize" leaves the default surface
  preference, so the binary rewrites to the decoy — fails the attach + rematerialize tests.
- "Write JSON receipts" (the shape the broken writer emits) fails the key=value receipt
  test and the attach gate because the binary only honors key=value receipts.
- "Activate at the surface path" fails the pool-state test even when UUID/receipt are right.

### Per-gate Pitfall Inventory
- RC1/RC7/GX3: oracle rewrites four helpers with real resolution/staging logic (~90 LOC),
  not flag flips; the one drop-in value flip is a minority of the delta.
- RC2: oracle-touched files use opaque names (fold_g/seat_r/mark_c/tidy_v/pref_k, 10-select.conf).
- RC3/RC4/RC5: tests assert domain-correct UUIDs/paths/receipt bytes computed in test code
  from the journal+seal+roster, never read from an environment golden file.
- RC6/GX9/GX10: instruction is symptoms-only; no schema enumeration recital, no per-disk
  value table, no both-polarity phrasing for attached.
- CR7: instruction nouns (pool, disk, attach, uuid, receipt, authority) do not appear as
  symbols inside oracle-touched files.
- CR2/flipping: four distinct helper files + one drop-in each control a minority subset.
- NOP: report is absent (or attach_ok false with decoy UUIDs) before any work.

### Initial Draft Commitments
- tasks/libvirt-pool-attach-disk-seating/instruction.md
- tasks/libvirt-pool-attach-disk-seating/task.toml
- tasks/libvirt-pool-attach-disk-seating/output_contract.toml
- tasks/libvirt-pool-attach-disk-seating/environment/Dockerfile
- tasks/libvirt-pool-attach-disk-seating/environment/.dockerignore
- tasks/libvirt-pool-attach-disk-seating/environment/go.mod
- tasks/libvirt-pool-attach-disk-seating/environment/cmd/virtattach/main.go
- tasks/libvirt-pool-attach-disk-seating/environment/internal/planx/planx.go
- tasks/libvirt-pool-attach-disk-seating/environment/internal/planx/aux.go
- tasks/libvirt-pool-attach-disk-seating/environment/internal/seatx/seatx.go
- tasks/libvirt-pool-attach-disk-seating/environment/internal/seatx/xmlx.go
- tasks/libvirt-pool-attach-disk-seating/environment/internal/receiptx/receiptx.go
- tasks/libvirt-pool-attach-disk-seating/environment/internal/reportx/reportx.go
- tasks/libvirt-pool-attach-disk-seating/environment/ops/run_pool_attach.sh
- tasks/libvirt-pool-attach-disk-seating/environment/ops/fold_g.sh
- tasks/libvirt-pool-attach-disk-seating/environment/ops/seat_r.sh
- tasks/libvirt-pool-attach-disk-seating/environment/ops/mark_c.sh
- tasks/libvirt-pool-attach-disk-seating/environment/ops/tidy_v.sh
- tasks/libvirt-pool-attach-disk-seating/environment/ops/pref_k.sh
- tasks/libvirt-pool-attach-disk-seating/environment/etc/libvirt/storage/pool_alpha.xml
- tasks/libvirt-pool-attach-disk-seating/environment/etc/libvirt/storage/pool_beta.xml
- tasks/libvirt-pool-attach-disk-seating/environment/etc/libvirt/storage/pool_gamma.xml
- tasks/libvirt-pool-attach-disk-seating/environment/etc/libvirt/storage/pool_delta.xml
- tasks/libvirt-pool-attach-disk-seating/environment/etc/libvirt/storage/pool_omega.xml
- tasks/libvirt-pool-attach-disk-seating/environment/etc/libvirt/storage/attach.seal
- tasks/libvirt-pool-attach-disk-seating/environment/etc/libvirt/qemu/dom_web.xml
- tasks/libvirt-pool-attach-disk-seating/environment/etc/libvirt/qemu/dom_db.xml
- tasks/libvirt-pool-attach-disk-seating/environment/etc/libvirt/qemu/dom_cache.xml
- tasks/libvirt-pool-attach-disk-seating/environment/etc/libvirt/qemu/dom_edge.xml
- tasks/libvirt-pool-attach-disk-seating/environment/etc/libvirt/qemu/seat.roster
- tasks/libvirt-pool-attach-disk-seating/environment/etc/libvirt/qemu/attach.d/10-select.conf
- tasks/libvirt-pool-attach-disk-seating/environment/var/lib/libvirt/ops/cutover.journal
- tasks/libvirt-pool-attach-disk-seating/environment/var/lib/libvirt/ops/receipts/.keep
- tasks/libvirt-pool-attach-disk-seating/environment/var/run/libvirt/.keep
- tasks/libvirt-pool-attach-disk-seating/environment/data/pools/alpha.img
- tasks/libvirt-pool-attach-disk-seating/environment/data/pools/beta.img
- tasks/libvirt-pool-attach-disk-seating/environment/data/pools/gamma.img
- tasks/libvirt-pool-attach-disk-seating/environment/data/pools/delta.img
- tasks/libvirt-pool-attach-disk-seating/environment/docs/layout.md
- tasks/libvirt-pool-attach-disk-seating/environment/docs/operator-notes.md
- tasks/libvirt-pool-attach-disk-seating/solution/solve.sh
- tasks/libvirt-pool-attach-disk-seating/tests/test.sh
- tasks/libvirt-pool-attach-disk-seating/tests/test_outputs.py

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table
```
- path: ops/fold_g.sh
  symbol: (script)
  kind: function
  signature: resolves durable identity+path per roster pool from the cutover journal capped by the seal; writes seating plan
  purpose: joins roster + journal + seal into the plan the sealed binary consumes
- path: ops/seat_r.sh
  symbol: (script)
  kind: function
  signature: seeds pool runtime state active at the durable target path
  purpose: creates /var/lib/libvirt/storage/<pool> state
- path: ops/mark_c.sh
  symbol: (script)
  kind: function
  signature: writes key=value cutover receipts per roster disk
  purpose: authorizes attach for the sealed binary
- path: ops/tidy_v.sh
  symbol: (script)
  kind: function
  signature: removes torn .part/.lock markers
  purpose: clean lease state
- path: etc/libvirt/qemu/attach.d/10-select.conf
  symbol: (config)
  kind: constant
  signature: authority=<mode>
  purpose: selection preference read by the sealed binary
```

#### flipping_point_contract
```
locations:
  - id: A
    path: ops/fold_g.sh
    controls_tests: [test_j4_slate, test_p8_quartz, test_w2_onyx, test_r5_flint]
  - id: B
    path: ops/seat_r.sh
    controls_tests: [test_k9_marl, test_r5_flint]
  - id: C
    path: ops/mark_c.sh
    controls_tests: [test_c3_ochre, test_r5_flint]
  - id: D
    path: ops/tidy_v.sh
    controls_tests: [test_t7_umber, test_d1_slate2]
  - id: E
    path: etc/libvirt/qemu/attach.d/10-select.conf
    controls_tests: [test_m6_verd, test_x9_bait]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest
```
- path: internal/reportx/reportx.go
  kind: module
  rhymes_with: A
  non_fix_purpose: serializes the report JSON from live state (sealed, correct)
- path: internal/seatx/xmlx.go
  kind: module
  rhymes_with: A
  non_fix_purpose: rewrites domain disk source per preference (sealed, correct)
- path: ops/run_pool_attach.sh
  kind: helper
  rhymes_with: A
  non_fix_purpose: entrypoint that chains helpers then execs the sealed binary
```

#### code_forbidden_tokens
```
code_forbidden_tokens: [pool, disk, domain, uuid, receipt, attach, authority, seating, source, volume, durable, surface, active, journal, seal, roster, health, cutover, storage]
```
