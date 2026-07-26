### Decision
GO — Attempt 1. Ops-only ingest cutover (no repair/debug framing): C io_uring fixed-buffer registry × Go lease broker × sealed-journal preflight authority; opaque symbols; false-green healthctl; decoy live profiles.

### Metadata
- version: 2
- Task name: iouring-registered-buffer-lease-cutover
- Title: io_uring Buffer Lease Cutover
- Category: system-administration
- Languages: ["C", "Go"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: []
- Tags: ["io-uring", "mount", "namespaces", "leases", "ops", "c"]
- Milestones: 0

## Authoring Brief

### Public contract

A single-container ingest broker lab simulates io_uring fixed-buffer registration and per-tenant mount-namespace leases under `/data/lab/`. Three tenants — `ten-alpha`, `ten-beta`, `ten-gamma` — belong to the broker. After a lease rollover, surface health still reports OK while jobs see stale registered buffers, wrong PrivateMounts for tenant trees, or leases that preflight rewrites from the sealed journal. Decoy config profiles look live.

**Symptoms the agent sees (instruction.md level):**
- Surface health reports OK after the lease rollover.
- Jobs see stale registered buffers.
- Wrong PrivateMounts for tenant trees.
- Leases that preflight rewrites from the sealed journal.
- Config profiles look live even when not authoritative for the durable lease map.

**Required outcomes:**
- `/output/lease-cutover.json` exists with integer `version` `1` and array `tenants`. Each row has string `tenant`, string `buf_slot`, string `mount_ns` (`broker` or `host`), integer `lease_epoch`, boolean `buf_fresh`, boolean `preflight_stable`.
- All three broker-owned tenants appear with `mount_ns` `broker`, `buf_fresh` true, `preflight_stable` true, and `lease_epoch` equal to the durable lease map epoch.
- `buf_slot` matches the on-disk registry slot id for that tenant under the broker ring tree.
- Unit `PrivateMounts` must not block tenant seating (`PrivateMounts=no` on the live fragment and drop-in).
- A re-run of preflight leaves the durable lease map and buffer registry unchanged.
- Seeded tree under `/data/fixtures/ingest-seed/` unchanged.

**Constraints:**
- `[environment] allow_internet = false`; verifier deps in Dockerfile.
- No multi-container layout.
- Agent performs ops cutover using bundled C + Go CLIs — not repair/debug framing.
- Language surface is C (io_uring worker helpers) + Go (lease broker) + unit fragments + bash wrappers.
- Kernel io_uring is simulated via lab ledgers (no privileged docker flags).

### Failure topology

Three interacting clusters. First, false-green surface: `healthctl` checks unit active plus any buffer file presence and ignores registry generation, mount-ns identity, and journal seal. Second, buffer vs lease: fixed-buffer slots remain under host with stale generation unless registration agrees with the durable lease epoch from the Go broker. Third, preflight authority: naive PrivateMounts or live-map edits are rewritten from the sealed journal unless the seal tip matches the durable epoch; decoy harbor profiles look authoritative for the live map.

Hard because no single CLI documents full order. `nsprobe` exposes truth; `bufreg`, `leasectl`, and `ledgerout` mutate distinct subsystems; wrong order or decoy profile keeps `healthctl` green while preflight undoes shallow edits.

### Environment shape

- `environment/Dockerfile` + `.dockerignore` — GCC + Go build, python3/pytest, seeded lab under `/data/lab/`.
- `environment/cmd/` — opaque CLIs: `healthctl`, `nsprobe`, `bufreg`, `nsbind`, `leasectl`, `preflight`, `jobpulse`, `ledgerout`.
- `environment/ring/` — `fold_a` fix-path + `skim_fold` decoy.
- `environment/mesh/` — `SieveB` fix-path + `SkimSieve` decoy (Go).
- `environment/roll/` — `emit_c` fix-path.
- `environment/lib/` — shared state_io / path helpers.
- `environment/units/` — ingest unit fragments.
- `environment/config/` — lab/fleet/harbor profiles and sparse field notes (no seating formula).
- `environment/scripts/` — status wrappers and cutover stub.
- `environment/data/` — fixture builder + ingest-seed anchor.

### Required artifacts

- `tasks/iouring-registered-buffer-lease-cutover/task.toml` with `allow_internet = false`, `category = "system-administration"`.
- `instruction.md` — symptoms-only; names output path and JSON fields.
- `tests/test.sh`, `tests/test_outputs.py` — six opaque hard tests.
- `solution/solve.sh` — oracle rebuilds fix-path bodies then ops sequence (≥30 LOC).
- `environment/**` — 25+ non-Docker files per Initial Draft Commitments.

### Test plan

- `test_n4_quartz` — mount_ns is `broker` for all three tenants; broker tree seated; host markers absent.
- `test_p7_jasper` — buf_fresh true; on-disk registry generation matches durable lease epoch (not decoy).
- `test_r2_citrine` — lease_epoch matches durable map and fleet profile for every tenant.
- `test_k8_fluorite` — PrivateMounts=no on live unit and drop-in; seating not blocked.
- `test_w3_beryl` — re-run preflight leaves durable map + registry unchanged; preflight_stable true.
- `test_y6_spinel` — ledger schema version 1 + tenants fields; ingest-seed checksums intact; buf_slot strings match on-disk slots.

Multiple valid CLI sequences allowed if outcomes match. Chain-dependent: preflight/schema tests need prior registration+lease+fold.

### Drafting guardrails

Do not embed instruction nouns in fix-path symbols, parameters, or test names. Instruction may use standard ops language. No repair/debug TODOs. healthctl must genuinely implement shallow checks. No HINT walkthroughs under environment/. Field notes must not spell register→enter→bind order or name which profile is “ignore me.”

### Triviality Ledger

- Calling skim_fold (host/stale gen) passes healthctl but fails buf_fresh and mount seating.
- Editing PrivateMounts alone fails because preflight rewrites from sealed journal unless SieveB updates the seal.
- Writing only the live lease map from harbor passes surface checks but fails durable epoch and preflight_stable.
- Seating without fold_a leaves stale buffers → test_p7_jasper fails.
- ledgerout without unit fold fails PrivateMounts test.
- Touching ingest-seed fails checksum expectations inside schema test.

### Per-gate Pitfall Inventory

- RC1: Oracle adds CLI/rebuild logic only — never delete-bug or wholesale restore golden.
- RC3: Tests assert mount_ns, buf_fresh, lease_epoch, preflight stability — not mere file existence.
- RC5: Expected epoch and slot tokens live in test code / fleet profile reads, not golden under environment/.
- RC6: Instruction symptoms-only — no fold_a / register order / fleet.toml named as fix.
- RC7: solve.sh rebuild + CLI chain ≥30 substantive LOC.
- CR1/CR2: Construction manifest symbols verbatim; 2+2+2 flip split.
- CR7/GX9: JSON field names in instruction; order only in runtime.
- Static: allow_internet=false, .dockerignore, absolute paths, category system-administration.
- Fanotify lesson: no seating formula in field-notes; fair report contract for all tenants.

### Initial Draft Commitments

- `tasks/iouring-registered-buffer-lease-cutover/task.toml`
- `tasks/iouring-registered-buffer-lease-cutover/instruction.md`
- `tasks/iouring-registered-buffer-lease-cutover/output_contract.toml`
- `tasks/iouring-registered-buffer-lease-cutover/tests/test.sh`
- `tasks/iouring-registered-buffer-lease-cutover/tests/test_outputs.py`
- `tasks/iouring-registered-buffer-lease-cutover/solution/solve.sh`
- `tasks/iouring-registered-buffer-lease-cutover/environment/Dockerfile`
- `tasks/iouring-registered-buffer-lease-cutover/environment/.dockerignore`
- `tasks/iouring-registered-buffer-lease-cutover/environment/Makefile`
- `tasks/iouring-registered-buffer-lease-cutover/environment/go.mod`
- `tasks/iouring-registered-buffer-lease-cutover/environment/include/lab.h`
- `tasks/iouring-registered-buffer-lease-cutover/environment/include/state.h`
- `tasks/iouring-registered-buffer-lease-cutover/environment/lib/state_io.c`
- `tasks/iouring-registered-buffer-lease-cutover/environment/lib/state_io.h`
- `tasks/iouring-registered-buffer-lease-cutover/environment/lib/path_util.c`
- `tasks/iouring-registered-buffer-lease-cutover/environment/lib/path_util.h`
- `tasks/iouring-registered-buffer-lease-cutover/environment/ring/fold_a.c`
- `tasks/iouring-registered-buffer-lease-cutover/environment/ring/fold_a.h`
- `tasks/iouring-registered-buffer-lease-cutover/environment/ring/skim_fold.c`
- `tasks/iouring-registered-buffer-lease-cutover/environment/ring/skim_fold.h`
- `tasks/iouring-registered-buffer-lease-cutover/environment/mesh/sieve_b.go`
- `tasks/iouring-registered-buffer-lease-cutover/environment/mesh/skim_sieve.go`
- `tasks/iouring-registered-buffer-lease-cutover/environment/roll/emit_c.c`
- `tasks/iouring-registered-buffer-lease-cutover/environment/roll/emit_c.h`
- `tasks/iouring-registered-buffer-lease-cutover/environment/cmd/healthctl/main.c`
- `tasks/iouring-registered-buffer-lease-cutover/environment/cmd/nsprobe/main.c`
- `tasks/iouring-registered-buffer-lease-cutover/environment/cmd/bufreg/main.c`
- `tasks/iouring-registered-buffer-lease-cutover/environment/cmd/nsbind/main.c`
- `tasks/iouring-registered-buffer-lease-cutover/environment/cmd/ledgerout/main.c`
- `tasks/iouring-registered-buffer-lease-cutover/environment/cmd/jobpulse/main.c`
- `tasks/iouring-registered-buffer-lease-cutover/environment/cmd/leasectl/main.go`
- `tasks/iouring-registered-buffer-lease-cutover/environment/cmd/preflight/main.go`
- `tasks/iouring-registered-buffer-lease-cutover/environment/units/ingest.service`
- `tasks/iouring-registered-buffer-lease-cutover/environment/units/10-private.conf`
- `tasks/iouring-registered-buffer-lease-cutover/environment/config/lab.toml`
- `tasks/iouring-registered-buffer-lease-cutover/environment/config/fleet.toml`
- `tasks/iouring-registered-buffer-lease-cutover/environment/config/harbor.toml`
- `tasks/iouring-registered-buffer-lease-cutover/environment/config/field-notes.md`
- `tasks/iouring-registered-buffer-lease-cutover/environment/scripts/status-top.sh`
- `tasks/iouring-registered-buffer-lease-cutover/environment/scripts/cutover-stub.sh`
- `tasks/iouring-registered-buffer-lease-cutover/environment/data/build_fixtures.sh`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: ring/fold_a.c
  symbol: fold_a
  kind: function
  signature: int fold_a(const char *a, const char *b)
  purpose: Writes fixed-buffer registry slots and generation under the broker ring tree from durable epoch state.

- path: mesh/sieve_b.go
  symbol: SieveB
  kind: function
  signature: func SieveB(a string, b string) error
  purpose: Writes the durable lease map and journal seal tip from the fleet profile epoch.

- path: roll/emit_c.c
  symbol: emit_c
  kind: function
  signature: int emit_c(const char *a, const char *b)
  purpose: Folds unit PrivateMounts, seats tenant markers into the broker mount tree, and writes lease-cutover.json.
```

#### flipping_point_contract

```
locations:
  - id: A
    path: ring/fold_a.c
    controls_tests: [test_p7_jasper, test_y6_spinel]
  - id: B
    path: mesh/sieve_b.go
    controls_tests: [test_r2_citrine, test_w3_beryl]
  - id: C
    path: roll/emit_c.c
    controls_tests: [test_n4_quartz, test_k8_fluorite]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: ring/skim_fold.c
  kind: helper
  rhymes_with: fold_a
  non_fix_purpose: Registers buffer slots under the host tree with a stale generation used by diagnostic scripts.

- path: mesh/skim_sieve.go
  kind: helper
  rhymes_with: SieveB
  non_fix_purpose: Writes the live (non-durable) lease map from the harbor profile without updating the journal seal.
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [surface, health, ingest, broker, lab, lease, rollover, jobs, registered, buffers, PrivateMounts, tenant, trees, preflight, sealed, journal, config, profiles, authoritative, durable, map, cutover, fixed-buffer, registrations, mount, namespace, epoch, seating, registry, fixtures, ingest-seed, output, version, tenants, array, row, buf_slot, mount_ns, lease_epoch, buf_fresh, preflight_stable, booleans, integer, string, on-disk, slot, id, host]
```
