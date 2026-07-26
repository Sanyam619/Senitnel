### Decision
GO — Attempt 1. Hard system-administration OpenLDAP syncrepl consumer seating with coupled CSN journal tip × provider prefer fold × hold windows × surface rematerialize × ledger emit. No application-debug frontier; live `/etc/ldap` + `/var/lib/ldap` seating.

### Metadata
- version: 2
- Task name: openldap-syncrepl-consumer-tip-lattice
- Title: LDAP Syncrepl Seating
- Category: system-administration
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["openldap", "syncrepl", "contextcsn", "provider-prefer", "hold-window", "ops-seating"]
- Milestones: 0

## Authoring Brief

### Public contract
Live directory consumer materials under `/etc/ldap/slapd.d/` and
`/var/lib/ldap/` must agree with durable prefer + CSN journal authority under
`/var/lib/ldap/ops/`. Entrypoint `/app/ops/run_ldap_seat.sh` must produce
`/output/ldap-seat.json` with:

- `schema_tag` (string) equal to `ldap-seat-v1`
- `consumers` — array of `{name, provider, contextCSN, generation, bound}`
- `holds` — array of `{suffix, until_epoch}`
- `sync_ok` (boolean)

A consumer is bound only when `contextCSN` matches the durable journal tip for
that suffix, `generation` ≥ durable floor, `provider` is the prefer-selected
URI (not the surface decoy), and the suffix is not under an active hold.
Surface `/usr/local/bin/ldaphealth` may print in-sync while `sync_ok` is false.
Frozen LDIF samples under `/app/data/ldap/` stay integrity-pinned. Two seating
runs must leave byte-identical `/output/ldap-seat.json`. Verifier re-invokes
seating and rejects hand-authored JSON.

### Failure topology
Authorities couple: lexical prefer.d fold (last-wins URI), durable CSN journal
tip for sealed gen (not newest live row / live contextCSN sheets), generation
vs durable floors (live floors disagree), hold expiry vs desk clock, surface
URI rematerialize into slapd.d consumer configs unless prefer.accept matches
the journal tip id, and ledger emit that sets `bound`/`sync_ok` only on full
agreement. Greening ldaphealth or fixing cn=config alone still fails journal
tip and decoy provider cells.

### Environment shape
- Broken ops helpers under `/app/rim`, `/app/ops`, `/app/bag`, `/app/deck`
- Decoy helpers under `/app/wire` and extra rim/bag scripts
- Live host state under `/etc/ldap`, `/var/lib/ldap`
- Immutable LDIF fixtures under `/app/data/ldap` plus packaging digests
- Outcome docs under `/app/docs`
- Correct seating publisher invoked after helpers prepare live state

### Required artifacts
Standard layout: `instruction.md`, `task.toml`, `output_contract.toml`,
`environment/` (≥20 files excl. Docker), `solution/solve.sh`,
`tests/{test.sh,test_outputs.py}`, `environment/.dockerignore`, hashed
`requirements.txt`.

### Test plan
- `test_q3_topaz` — ledger schema + schema_tag + sync_ok true
- `test_n4_beryl` — double-run byte-identical output
- `test_w7_quartz` — `/app/data/ldap` packaging digest pin
- `test_j2_onyx` — lexical prefer fold selects durable provider URI
- `test_v5_coral` — generation ≥ durable floor polarity across roster
- `test_p9_jade` — active vs expired hold windows on bound bits
- `test_h8_amber` — surface rematerialize suppressed; provider not decoy
- `test_c1_flint` — prefer.accept tip id + gen.live aligned
- `test_r6_slate` — contextCSN equals durable journal tip per consumer
- `test_u2_mica` — holds array contents + sync_ok coupling
- `test_m1_opal` — full roster bound/unbound matrix
- `test_t4_pearl` — ldaphealth may print in-sync while deep seating required
- `test_k5_garnet` — novel sealed-journal tip inject shifts CSN+gen together

Each test accepts any correct seating end-state; none require oracle-only paths.
Not chain-dependent: each can set up via full entrypoint re-entry.

### Drafting guardrails
Symptoms-only instruction; fair outcomes in `/app/docs` (receipt format,
bound rules). Opaque fix-path symbols from construction manifest. No intent
comments. No golden JSON under environment. Verifier re-enters seating and
derives EXPECTED from durable fixtures.

### Triviality Ledger
- Hand-writing `/output/ldap-seat.json` fails because verifier deletes output and re-enters `/app/ops/run_ldap_seat.sh` twice.
- Editing only slapd.d providerURI fails because `helm_w` rematerializes surface URI unless matching `prefer.accept`.
- Using live `/etc/ldap/floors` or live contextCSN sheets fails distant generation/CSN cells against durable floors/journal.
- Ignoring hold expiry greens wrong bound bits on the hold-bound suffix.
- First-wins prefer fold keeps surface decoy provider on every consumer.
- Leaving `sync_ok` always true fails when any consumer disagrees.
- Hardcoding the sealed tip fails `test_k5_garnet` novel inject.

### Per-gate Pitfall Inventory
- RC1: oracle rewrites substantive helper bodies (not delete BUG markers).
- RC2: no broken_/golden_/expected_ names on solver-visible surfaces.
- RC3: tests assert computed bound/provider/CSN values, not schema alone.
- RC4/RC5: EXPECTED in tests; no golden under environment/.
- RC6: instruction symptoms-only; outcomes not fix recipes.
- RC7: oracle LOC ≥30 substantive lines.
- GX9/GX10: no per-consumer answer-key recital; no polarity contradiction in one sentence.
- Static: `allow_internet=false`; hashed requirements; PLW1510 `check=`; `.dockerignore`.
- Category: grade live `/etc`/`/var` via bash ops; languages=`["bash"]`; no repair framing.

### Initial Draft Commitments
- instruction.md
- task.toml
- output_contract.toml
- construction_manifest.json
- solution/solve.sh
- tests/test.sh
- tests/test_outputs.py
- environment/Dockerfile
- environment/.dockerignore
- environment/requirements.txt
- environment/ops/run_ldap_seat.sh
- environment/ops/axle_y.sh
- environment/ops/helm_w.sh
- environment/rim/mesh_x.sh
- environment/rim/scan_m.sh
- environment/bag/skim_z.sh
- environment/bag/note_t.sh
- environment/deck/emit_q.sh
- environment/wire/knit_p.sh
- environment/cli/seatctl
- environment/cli/ldaphealth
- environment/docs/layout.md
- environment/docs/seating_contract.md
- environment/docs/operator-notes.md
- environment/config/site_standard.conf
- environment/packaging/ldap.sha256
- environment/packaging/README.md
- environment/data/ldap/alpha.ldif
- environment/data/ldap/beta.ldif
- environment/data/ldap/gamma.ldif
- environment/data/ldap/delta.ldif
- environment/data/ldap/epsilon.ldif
- environment/data/roster.list
- environment/data/seed/floors.toml
- environment/data/seed/live_floors.toml
- environment/data/seed/holds.toml
- environment/data/seed/journal.jsonl
- environment/data/seed/clock.epoch
- environment/data/seed/surface.uri
- environment/data/seed/prefer.d/10-surface.conf
- environment/data/seed/prefer.d/40-lab.conf
- environment/data/seed/prefer.d/90-local.conf
- environment/data/seed/slapd.d/cn=config/olcDatabase=mdb.ldif
- environment/data/build_fixtures.sh

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: rim/mesh_x.sh
  symbol: mesh_x
  kind: function
  signature: mesh_x
  purpose: Lexically fold prefer.d keys into effective provider policy
- path: ops/axle_y.sh
  symbol: axle_y
  kind: function
  signature: axle_y
  purpose: Resolve sealed journal tip and align generations to durable floors
- path: bag/skim_z.sh
  symbol: skim_z
  kind: function
  signature: skim_z
  purpose: Materialize hold windows against desk clock
- path: ops/helm_w.sh
  symbol: helm_w
  kind: function
  signature: helm_w
  purpose: Rematerialize surface provider URI unless prefer.accept matches tip
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
    controls_tests: [test_v5_coral, test_c1_flint, test_m1_opal, test_k5_garnet]
  - id: C
    path: bag/skim_z.sh
    controls_tests: [test_p9_jade, test_u2_mica, test_t4_pearl]
  - id: D
    path: ops/helm_w.sh
    controls_tests: [test_h8_amber, test_c1_flint, test_n4_beryl, test_r6_slate]
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
  non_fix_purpose: Writes operator status crumbs under /var/log/ldap; not on seating path
- path: rim/scan_m.sh
  kind: helper
  rhymes_with: axle_y
  non_fix_purpose: Counts directory entries for ldaphealth surface check
- path: bag/note_t.sh
  kind: helper
  rhymes_with: skim_z
  non_fix_purpose: Archives a non-graded hold memo copy
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [directory, consumer, replication, schema_tag, consumers, provider, contextCSN, generation, bound, holds, suffix, until_epoch, sync_ok, slapd, durable, prefer, journal, ldaphealth, samples, entrypoint, seating, verifier, syncrepl, rematerialize, floor, tip, decoy, hold, window, roster, lexical, receipt, surface]
```
