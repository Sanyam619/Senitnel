### Decision
GO — Attempt 1. Hard system-administration systemd-nspawn machine bind seating with coupled durable image-tip × same-inode Bind= attach × machines.target fold × generation floors × abort rematerialize receipt × ledger emit. No application-debug frontier; primary activity is live `/etc`/`/var` machine seating.

### Metadata
- version: 2
- Task name: nspawn-machine-bind-seating
- Title: Nspawn Bind Seating
- Category: system-administration
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["nspawn", "machine-seating", "bind-attach", "image-tip", "generation-gate", "ops-journal"]
- Milestones: 0

## Authoring Brief

### Public contract
Live systemd-nspawn seating under `/etc/systemd/nspawn/` and
`/etc/systemd/system/machines.target.wants/` must agree with durable machine
authority under `/var/lib/machines/`. Entrypoint
`/app/ops/run_nspawn_seat.sh` must produce `/output/nspawn-seat.json` with:

- `schema_tag` (string) equal to `nspawn-seat-v1`
- `machines` — array of `{name, root, bind, generation, active}`
- `ports` — array of `{machine, host, container}`
- `seat_ok` (boolean)

A machine is active only when its `root` is the durable image tip (not the
live shadow root), every `Bind=` path is same-inode-attached to the sealed
volume under `/var/lib/machines/volumes/`, and generation ≥ durable floor.
Surface `/usr/local/bin/machinectl-health` may report running while
`seat_ok` is false. Frozen images under `/app/data/machines/` stay
integrity-pinned. Two seating runs must leave byte-identical output.
Verifier re-runs seating after wiping `/output`.

### Failure topology
Authorities couple: durable image tip vs live shadow root, same-inode Bind=
attach (string-equal paths that are different inodes fail), lexical
machines.target.wants fold with abort override, durable generation floors
(live decoy floors disagree), abort.d rematerialize unless durable
`cutover.ok` (`key=value`, `gen=<target>`, `mode=seal`) while live
`90-local.conf` stays present with site-standard tokens, port ledger from
durable ops journal, and ledger emit that sets `seat_ok` only on full
agreement. Greening health or rewriting one unit still fails distant cells.

### Environment shape
- Live nspawn units and machines.target.wants drop-ins under `/etc/systemd/`
- Durable images, sealed volumes, floors, prefer/bind journal under `/var/lib/machines/`
- Ops entrypoint + opaque helpers under `/app/ops`, `/app/rim`, `/app/bag`, `/app/deck`, `/app/wire`
- Surface health bait under `/usr/local/bin/machinectl-health`
- Frozen packaging digests under `/app/packaging/`
- Contract docs under `/app/docs/`

### Required artifacts
Standard layout: `instruction.md`, `task.toml`, `output_contract.toml`,
`environment/` (≥20 files excl. Docker), `solution/solve.sh`,
`tests/{test.sh,test_outputs.py}`. Hashed `requirements.txt` +
`.dockerignore`. No multi-container / UI.

### Test plan
At least 12 non-trivial tests (opaque mineral names). Cover: schema +
`seat_ok`; idempotent double seat; frozen image pin; durable root tip (not
live shadow); same-inode Bind= attach; generation×floor polarity; lexical
fold site-standard; abort forensic vs live rewrite; cutover receipt;
ports ledger; full active matrix; surface health bait while deep seating
required. No existence-only or format-only free cells.

### Drafting guardrails
Symptoms-only instruction (no helper names as fix recipe, no inode algebra
checklist). Opaque fix-path symbols. No intent comments on fix path. Docs
state fair outcomes (durable tip, same-inode, floor equality, receipt
format) without greppable knob checklists of answer values. Do not frame
as repair/debug of application source.

### Triviality Ledger
- String-equal Bind= copy without hardlink greens naive path equality but
  fails same-inode attach cells.
- Preferring live shadow root greens process-presence health but fails tip
  and `seat_ok` cells.
- Deleting live `90-local.conf` to clear abort fails fold presence + receipt
  coupling; matching `cutover.ok` must skip rematerialize while live file
  stays site-standard.
- Live floors sheet alone fails durable floor polarity on under-floor
  machines.
- Hand-written JSON without re-entry fails verifier wipe-and-reseat.

### Per-gate Pitfall Inventory
- RC1: oracle rewrites helper bodies with substantive tip/inode/fold logic,
  not sed-delete of BUG markers.
- RC2: mineral test names; no broken_/golden_ tokens on solver surfaces.
- RC3: tests assert tip path, inode equality, gen/floor, ports, matrix —
  not schema-only.
- RC4/RC5: EXPECTED recomputed from durable `/var` + journal inside tests;
  no golden JSON under environment.
- RC6: instruction symptoms-only; contract detail in docs as outcomes.
- RC7: solve.sh ≥80 substantive LOC rewriting multiple helpers.
- GX9/GX10: no per-machine answer recital or polarity contradictions in
  instruction.
- Static: allow_internet=false; hashed pip; PLW1510 check=; .dockerignore.

### Initial Draft Commitments
- tasks/nspawn-machine-bind-seating/instruction.md
- tasks/nspawn-machine-bind-seating/task.toml
- tasks/nspawn-machine-bind-seating/output_contract.toml
- tasks/nspawn-machine-bind-seating/solution/solve.sh
- tasks/nspawn-machine-bind-seating/tests/test.sh
- tasks/nspawn-machine-bind-seating/tests/test_outputs.py
- tasks/nspawn-machine-bind-seating/environment/Dockerfile
- tasks/nspawn-machine-bind-seating/environment/.dockerignore
- tasks/nspawn-machine-bind-seating/environment/requirements.txt
- tasks/nspawn-machine-bind-seating/environment/ops/run_nspawn_seat.sh
- tasks/nspawn-machine-bind-seating/environment/ops/axle_k.sh
- tasks/nspawn-machine-bind-seating/environment/ops/helm_w.sh
- tasks/nspawn-machine-bind-seating/environment/rim/mesh_p.sh
- tasks/nspawn-machine-bind-seating/environment/bag/knit_v.sh
- tasks/nspawn-machine-bind-seating/environment/bag/skim_z.sh
- tasks/nspawn-machine-bind-seating/environment/deck/emit_q.sh
- tasks/nspawn-machine-bind-seating/environment/wire/note_t.sh
- tasks/nspawn-machine-bind-seating/environment/cli/machinectl-health
- tasks/nspawn-machine-bind-seating/environment/cli/seatctl
- tasks/nspawn-machine-bind-seating/environment/docs/seating_contract.md
- tasks/nspawn-machine-bind-seating/environment/docs/layout.md
- tasks/nspawn-machine-bind-seating/environment/docs/operator-notes.md
- tasks/nspawn-machine-bind-seating/environment/config/site_standard.conf
- tasks/nspawn-machine-bind-seating/environment/data/roster.list
- tasks/nspawn-machine-bind-seating/environment/data/build_fixtures.sh
- tasks/nspawn-machine-bind-seating/environment/data/machines/{alpha,beta,gamma,delta,epsilon}.img
- tasks/nspawn-machine-bind-seating/environment/data/seed/floors.toml
- tasks/nspawn-machine-bind-seating/environment/data/seed/live_floors.toml
- tasks/nspawn-machine-bind-seating/environment/data/seed/ports.toml
- tasks/nspawn-machine-bind-seating/environment/data/seed/live_ports.toml
- tasks/nspawn-machine-bind-seating/environment/data/seed/journal.jsonl
- tasks/nspawn-machine-bind-seating/environment/data/seed/clock.epoch
- tasks/nspawn-machine-bind-seating/environment/data/seed/nspawn.d/{alpha,beta,gamma,delta,epsilon}.nspawn
- tasks/nspawn-machine-bind-seating/environment/data/seed/machines.target.wants/{10-core,40-lab,90-local}.conf
- tasks/nspawn-machine-bind-seating/environment/data/seed/abort.d/90-local.conf
- tasks/nspawn-machine-bind-seating/environment/packaging/README.md

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: ops/axle_k.sh
  symbol: axle_k
  kind: function
  signature: axle_k()
  purpose: resolve tip generations and eligibility against durable floors and sealed journal tips
- path: rim/mesh_p.sh
  symbol: mesh_p
  kind: function
  signature: mesh_p()
  purpose: fold machines.target.wants drop-ins last-wins into effective policy
- path: bag/knit_v.sh
  symbol: knit_v
  kind: function
  signature: knit_v()
  purpose: same-inode attach Bind= paths onto sealed volume objects
- path: ops/helm_w.sh
  symbol: helm_w
  kind: function
  signature: helm_w()
  purpose: abort rematerialize gated by matching cutover receipt
- path: deck/emit_q.sh
  symbol: emit_q
  kind: function
  signature: emit_q()
  purpose: emit seating ledger with durable roots, bind lists, ports, seat_ok
- path: bag/skim_z.sh
  symbol: skim_z
  kind: function
  signature: skim_z()
  purpose: publish durable port rows into state for ledger emit
```

#### flipping_point_contract

```
locations:
  - id: A
    path: environment/ops/axle_k.sh
    controls_tests: [test_v5_coral, test_m1_opal, test_r6_slate]
  - id: B
    path: environment/bag/knit_v.sh
    controls_tests: [test_b3_zircon, test_m1_opal]
  - id: C
    path: environment/rim/mesh_p.sh
    controls_tests: [test_j2_onyx, test_h8_amber]
  - id: D
    path: environment/ops/helm_w.sh
    controls_tests: [test_h8_amber, test_c1_flint]
  - id: E
    path: environment/deck/emit_q.sh
    controls_tests: [test_q3_topaz, test_u2_mica, test_p8_garnet]
  - id: F
    path: environment/bag/skim_z.sh
    controls_tests: [test_p8_garnet]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: wire/note_t.sh
  kind: helper
  rhymes_with: emit_q
  non_fix_purpose: writes a surface status stamp under /var/run/machines; not graded
- path: cli/seatctl
  kind: helper
  rhymes_with: knit_v
  non_fix_purpose: prints unit inventory for operators; not authority
- path: cli/machinectl-health
  kind: helper
  rhymes_with: axle_k
  non_fix_purpose: process-presence surface OK bait
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [machine, machines, bind, seating, seat, root, tip, generation, floor, active, port, ports, nspawn, inode, attach, durable, shadow, abort, cutover, prefer, journal, roster, volume, schema, health]
```
