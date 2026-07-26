### Decision
GO — Attempt 1. Hard system-administration Pacemaker/Corosync cluster seating with coupled CIB stickiness fold × durable node generation × sealed fence-journal unretract × abort rematerialize receipt × deep seat emit. No application-debug frontier; primary activity is live `/etc`/`/var` ops seating via named entrypoint.

### Metadata
- version: 2
- Task name: pacemaker-fence-history-seating-lattice
- Title: Pacemaker Fence-History Seating Lattice
- Category: system-administration
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["pacemaker", "fence-journal", "cib-fold", "stickiness", "generation-gate", "ops-seating"]
- Milestones: 0

## Authoring Brief

### Public contract
Live cluster state under `/etc/corosync/`, `/etc/pacemaker/`, and
`/var/lib/pacemaker/` must agree with durable prefer + fence authority under
`/var/lib/cluster/ops/`. Entrypoint `/app/ops/run_crm_seat.sh` must produce
`/output/crm-seat.json` with:

- `schema_tag` (string) equal to `crm-seat-v1`
- `nodes` — array of `{name, online, generation}`
- `resources` — array of `{id, node, role, stickiness}`
- `fences` — array of `{target, epoch, status}`
- `seat_ok` (boolean)

Surface `/usr/local/bin/crmhealth` may print GREEN while deep seating is wrong.
Frozen fixtures under `/app/data/cluster/` stay integrity-pinned. A resource may
be `Started` on a node only when that node is online at durable generation,
resource stickiness matches the folded CIB drop-ins under
`/etc/pacemaker/cib.d/`, and no unretracted fence for that node appears in the
sealed fence journal with epoch strictly after the resource start epoch.
Two seating runs must leave byte-identical `/output/crm-seat.json`.

### Failure topology
Authorities couple: lexical CIB fold (later drop-ins override stickiness),
durable node generation from sealed prefer journal (live corosync sheets
disagree), unretracted fence after start epoch blocks `Started`, abort.d
rematerialize of naive location/stickiness drop-in unless durable
`cutover.ok` (`key=value`, `gen=<target>`, `mode=seal`) while live
`90-local.conf` stays present with site-standard tokens, and emit that sets
roles/sources/`seat_ok` only on full agreement. Greening crmhealth or one
resource still fails unretracted-fence and generation cells.

### Environment shape
- Broken ops helpers under `/app/rim`, `/app/ops`, `/app/bag`, `/app/deck`
- Decoy helpers under `/app/wire` and extra rim/bag scripts
- Live host state under `/etc/corosync`, `/etc/pacemaker`, `/var/lib/pacemaker`
- Durable ops under `/var/lib/cluster/ops`
- Immutable fixtures under `/app/data/cluster` plus packaging digests
- Outcome docs under `/app/docs`
- Correct seating publisher invoked after helpers prepare live state

### Required artifacts
Standard layout: `instruction.md`, `task.toml`, `output_contract.toml`,
`environment/` (≥20 files excl. Docker), `solution/solve.sh`,
`tests/{test.sh,test_outputs.py}`, `environment/.dockerignore`, hashed
`requirements.txt`.

### Test plan
- `test_q3_topaz` — ledger schema + schema_tag + seat_ok true
- `test_n4_beryl` — double-run byte-identical output
- `test_w7_quartz` — `/app/data/cluster` packaging digest pin
- `test_j2_onyx` — lexical CIB fold stickiness matches site standard
- `test_v5_coral` — node online/generation vs durable prefer polarity
- `test_p9_jade` — unretracted fence after start epoch blocks Started
- `test_h8_amber` — abort package forensic + live 90-local site-standard
- `test_c1_flint` — matching cutover.ok receipt; gen.live aligned
- `test_r6_slate` — full resource role/stickiness/node matrix
- `test_u2_mica` — fences array matches sealed unretract continuity
- `test_m1_opal` — nodes array + online bits against durable authority
- `test_k5_garnet` — retracted fence does not block later Started
- `test_s8_zircon` — wipe /output and re-enter seating still agrees
- `test_t4_pearl` — crmhealth may print GREEN; deep seat_ok still required

Each test accepts any correct seating end-state; none require oracle-only paths.
Not chain-dependent: each can set up via full entrypoint re-entry.

### Drafting guardrails
Symptoms-only instruction; fair outcomes in `/app/docs` (receipt format,
Started gate rules as scenarios). Opaque fix-path symbols from construction
manifest. No intent comments. No golden JSON under environment. Verifier
re-enters seating and derives EXPECTED from durable fixtures. No repair/debug
framing — grade seating outcomes on live cluster desks.

### Triviality Ledger
- Hand-writing `/output/crm-seat.json` fails because verifier deletes output
  and re-enters `/app/ops/run_crm_seat.sh` twice.
- Editing only live CIB drop-ins fails because `helm_r` rematerializes abort.d
  unless matching `cutover.ok`.
- Using live `/etc/corosync/nodes/` generations fails distant online cells
  against durable prefer tips.
- Ignoring unretracted fence greens wrong Started roles on fenced nodes.
- First-file-wins fold without later site-standard stickiness fails stickiness
  cells and Started gates.
- Leaving `seat_ok` always true fails when any resource/node disagrees.

### Per-gate Pitfall Inventory
- RC1: oracle rewrites substantive helper bodies (not delete BUG markers).
- RC2: no broken_/golden_/expected_ names on solver-visible surfaces.
- RC3: tests assert computed roles/online/stickiness/fence values, not schema alone.
- RC4/RC5: EXPECTED in tests; no golden under environment/.
- RC6: instruction symptoms-only; outcomes not fix recipes.
- RC7: oracle LOC ≥30 substantive lines.
- GX9/GX10: no per-resource answer-key recital; no polarity contradiction in one sentence.
- Static: `allow_internet=false`; hashed requirements; PLW1510 `check=`; `.dockerignore`.
- Category: grade live `/etc`/`/var` via bash ops; languages=`["bash"]`; no repair framing.

### Initial Draft Commitments
- instruction.md
- task.toml
- output_contract.toml
- solution/solve.sh
- tests/test.sh
- tests/test_outputs.py
- environment/Dockerfile
- environment/.dockerignore
- environment/requirements.txt
- environment/ops/run_crm_seat.sh
- environment/ops/axle_n.sh
- environment/ops/helm_r.sh
- environment/rim/mesh_k.sh
- environment/rim/scan_t.sh
- environment/bag/skim_p.sh
- environment/bag/note_u.sh
- environment/deck/emit_v.sh
- environment/wire/knit_q.sh
- environment/cli/seatctl
- environment/cli/crmhealth
- environment/docs/layout.md
- environment/docs/seating_contract.md
- environment/docs/operator-notes.md
- environment/config/site_standard.conf
- environment/packaging/cluster.sha256
- environment/packaging/README.md
- environment/data/cluster/* (roster, nodes, resources, fence samples)
- environment/data/seed/* (cib.d, abort.d, prefer journal, live decoys)
- environment/data/build_fixtures.sh

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: rim/mesh_k.sh
  symbol: mesh_k
  kind: function
  signature: mesh_k
  purpose: Lexically fold cib.d drop-in keys into effective CIB policy
- path: ops/axle_n.sh
  symbol: axle_n
  kind: function
  signature: axle_n
  purpose: Apply sealed prefer tips so node generations/online match durable
- path: bag/skim_p.sh
  symbol: skim_p
  kind: function
  signature: skim_p
  purpose: Materialize unretracted fence set from sealed fence journal
- path: ops/helm_r.sh
  symbol: helm_r
  kind: function
  signature: helm_r
  purpose: Rematerialize abort residue unless durable receipt matches
- path: deck/emit_v.sh
  symbol: emit_v
  kind: function
  signature: emit_v
  purpose: Publish seating ledger JSON from live+durable agreement
```

#### flipping_point_contract

```
locations:
  - id: A
    path: rim/mesh_k.sh
    controls_tests: [test_j2_onyx, test_r6_slate, test_w7_quartz]
  - id: B
    path: ops/axle_n.sh
    controls_tests: [test_v5_coral, test_m1_opal, test_c1_flint]
  - id: C
    path: bag/skim_p.sh
    controls_tests: [test_p9_jade, test_u2_mica, test_k5_garnet]
  - id: D
    path: ops/helm_r.sh
    controls_tests: [test_h8_amber, test_c1_flint, test_n4_beryl]
  - id: E
    path: deck/emit_v.sh
    controls_tests: [test_q3_topaz, test_r6_slate, test_s8_zircon, test_t4_pearl]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: wire/knit_q.sh
  kind: decoy_helper
  rhymes_with: axle_n
  non_fix_purpose: Seeds runtime lock dirs only; does not apply prefer tips
- path: rim/scan_t.sh
  kind: decoy_helper
  rhymes_with: mesh_k
  non_fix_purpose: Writes a surface inventory log crmhealth reads for GREEN
- path: bag/note_u.sh
  kind: decoy_helper
  rhymes_with: skim_p
  non_fix_purpose: Copies operator memo; never reads fence journal
- path: cli/crmhealth
  kind: surface_bait
  rhymes_with: seatctl
  non_fix_purpose: Prints GREEN from inventory without fence/generation checks
```

#### code_forbidden_tokens
["seat", "fence", "stickiness", "generation", "online", "crm", "pacemaker",
 "corosync", "journal", "retract", "started", "cib", "abort", "cutover"]
