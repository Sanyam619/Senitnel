### Decision
GO — Attempt 3. Hard system-administration autofs multi-map seating cutover with coupled drop-in fold × durable generation floors × hold windows × abort rematerialize receipt × ledger emit. No application-debug frontier.

### Metadata
- version: 2
- Task name: autofs-multi-map-seating-cutover
- Title: Autofs Map Seating
- Category: system-administration
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["autofs", "map-seating", "dropin-policy", "generation-gate", "ops-journal", "hold-window"]
- Milestones: 0

## Authoring Brief

### Public contract
Live automounter state under `/etc/auto.master.d/`, `/etc/autofs/`, and
`/var/lib/autofs/` must agree with durable map authority. Entrypoint
`/app/ops/run_autofs_seat.sh` must produce `/output/autofs-seat.json` with:

- `schema_tag` (string) equal to `autofs-seat-v1`
- `maps` — array of `{name, mountpoint, generation, source, active}`
- `holds` — array of `{key, until_epoch}`
- `seating_ok` (boolean)

Surface `/usr/local/bin/autofshealth` may print OK while deep seating is wrong.
Frozen fixtures under `/app/data/maps/` stay integrity-pinned. A map is active
only when generation ≥ durable floor, any hold window has not expired, and
lexical drop-in fold has no later abort override. Two seating runs must leave
byte-identical `/output/autofs-seat.json`.

### Failure topology
Authorities couple: lexical drop-in fold (abort override), durable generation
floors (live decoy floors disagree), hold expiry against desk clock, abort.d
rematerialize unless durable `cutover.ok` (`key=value`, `gen=<target>`,
`mode=seal`) while live `90-local.conf` stays present with site-standard
tokens, and ledger emit that sets `source` to durable map paths and
`seating_ok` only on full agreement. Greening health or one conf still fails
distant mineral tests.

### Environment shape
- Broken ops helpers under `/app/rim`, `/app/ops`, `/app/bag`, `/app/deck`
- Decoy helpers under `/app/wire` and extra rim/bag scripts
- Live host state under `/etc/auto.master.d`, `/etc/autofs`, `/var/lib/autofs`
- Immutable fixtures under `/app/data/maps` plus packaging digests
- Outcome docs under `/app/docs`
- Correct seating publisher invoked after helpers prepare live state

### Required artifacts
Standard layout: `instruction.md`, `task.toml`, `output_contract.toml`,
`environment/` (≥20 files excl. Docker), `solution/solve.sh`,
`tests/{test.sh,test_outputs.py}`, `environment/.dockerignore`, hashed
`requirements.txt`.

### Test plan
- `test_q3_topaz` — ledger schema + schema_tag + seating_ok true
- `test_n4_beryl` — double-run byte-identical output
- `test_w7_quartz` — `/app/data/maps` packaging digest pin
- `test_j2_onyx` — lexical fold effective policy matches site standard
- `test_v5_coral` — generation ≥ durable floor polarity across roster
- `test_p9_jade` — expired vs live hold windows
- `test_h8_amber` — abort override inactive map + abort.d forensic residue
- `test_c1_flint` — matching cutover.ok receipt; live 90-local present
- `test_r6_slate` — source paths under durable maps directory
- `test_u2_mica` — holds array contents + seating_ok coupling
- `test_m1_opal` — full roster active/inactive matrix
- `test_t4_pearl` — autofshealth may still print OK (surface≠deep not required fail)

Each test accepts any correct seating end-state; none require oracle-only paths.
Not chain-dependent: each can set up via full entrypoint re-entry.

### Drafting guardrails
Symptoms-only instruction; fair outcomes in `/app/docs` (receipt format,
seal/sealed vocabulary avoided — use documented cutover.ok keys). Opaque
fix-path symbols from construction manifest. No intent comments. No golden
JSON under environment. Verifier re-enters seating and derives EXPECTED from
durable fixtures.

### Triviality Ledger
- Hand-writing `/output/autofs-seat.json` fails because verifier deletes output and re-enters `/app/ops/run_autofs_seat.sh` twice.
- Editing only live drop-ins fails because `helm_w` rematerializes abort.d unless matching `cutover.ok`.
- Using live `/etc/autofs/floors` fails distant generation cells against durable floors.
- Ignoring hold expiry greens wrong active bits on the hold-bound map.
- Last-file-wins without abort key fails abort-suppressed map cell.
- Leaving `seating_ok` always true fails when any map disagrees.

### Per-gate Pitfall Inventory
- RC1: oracle rewrites substantive helper bodies (not delete BUG markers).
- RC2: no broken_/golden_/expected_ names on solver-visible surfaces.
- RC3: tests assert computed active/source/hold values, not schema alone.
- RC4/RC5: EXPECTED in tests; no golden under environment/.
- RC6: instruction symptoms-only; outcomes not fix recipes.
- RC7: oracle LOC ≥30 substantive lines.
- GX9/GX10: no per-map answer-key recital; no polarity contradiction in one sentence.
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
- environment/ops/run_autofs_seat.sh
- environment/ops/axle_y.sh
- environment/ops/helm_w.sh
- environment/rim/mesh_x.sh
- environment/rim/scan_m.sh
- environment/bag/skim_z.sh
- environment/bag/note_t.sh
- environment/deck/emit_q.sh
- environment/wire/knit_p.sh
- environment/cli/seatctl
- environment/cli/autofshealth
- environment/docs/layout.md
- environment/docs/seating_contract.md
- environment/docs/operator-notes.md
- environment/config/site_standard.conf
- environment/packaging/maps.sha256
- environment/packaging/README.md
- environment/data/maps/alpha.map
- environment/data/maps/beta.map
- environment/data/maps/gamma.map
- environment/data/maps/delta.map
- environment/data/maps/epsilon.map
- environment/data/roster.list
- environment/data/seed/floors.toml
- environment/data/seed/holds.toml
- environment/data/seed/journal.jsonl
- environment/data/seed/clock.epoch
- environment/data/seed/abort.d/90-local.conf
- environment/data/seed/auto.master.d/10-core.conf
- environment/data/seed/auto.master.d/40-lab.conf
- environment/data/seed/auto.master.d/90-local.conf
- environment/data/seed/live_floors.toml
- environment/data/build_fixtures.sh

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: rim/mesh_x.sh
  symbol: mesh_x
  kind: function
  signature: mesh_x
  purpose: Lexically fold drop-in conf keys into effective policy file
- path: ops/axle_y.sh
  symbol: axle_y
  kind: function
  signature: axle_y
  purpose: Apply journal cutover and align tip generations to durable floors
- path: bag/skim_z.sh
  symbol: skim_z
  kind: function
  signature: skim_z
  purpose: Materialize hold windows against desk clock
- path: ops/helm_w.sh
  symbol: helm_w
  kind: function
  signature: helm_w
  purpose: Rematerialize abort residue unless durable receipt matches
- path: deck/emit_q.sh
  symbol: emit_q
  kind: function
  signature: emit_q
  purpose: Publish seating ledger JSON from live+durable agreement
```

#### flipping_point_contract

```
locations:
  - id: A
    path: rim/mesh_x.sh
    controls_tests: [test_j2_onyx, test_h8_amber, test_m1_opal, test_w7_quartz]
  - id: B
    path: ops/axle_y.sh
    controls_tests: [test_v5_coral, test_c1_flint, test_m1_opal]
  - id: C
    path: bag/skim_z.sh
    controls_tests: [test_p9_jade, test_u2_mica, test_t4_pearl]
  - id: D
    path: ops/helm_w.sh
    controls_tests: [test_h8_amber, test_c1_flint, test_n4_beryl]
  - id: E
    path: deck/emit_q.sh
    controls_tests: [test_q3_topaz, test_r6_slate, test_u2_mica, test_n4_beryl]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: wire/knit_p.sh
  kind: helper
  rhymes_with: mesh_x
  non_fix_purpose: Writes operator status crumbs under /var/log/autofs
- path: rim/scan_m.sh
  kind: helper
  rhymes_with: axle_y
  non_fix_purpose: Lists roster names for autofshealth surface check
- path: bag/note_t.sh
  kind: helper
  rhymes_with: skim_z
  non_fix_purpose: Archives a non-graded hold memo copy
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [automounter, desk, autofs, map, authority, surface, autofshealth, seating, fixtures, integrity, operator, docs, layout, schema_tag, maps, name, mountpoint, generation, source, active, holds, key, until_epoch, seating_ok, floor, hold, window, drop-ins, dropins, abort, override, durable, receipt, cutover, rematerialize, site-standard, synonyms, forensic, entrypoint, roster, lexical, mode, seal, gen, target, clock, master]
```
