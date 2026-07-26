### Decision
GO — Attempt 1. Hard system-administration nftables ruleset seating cutover with coupled fragment fold × abort exclusion × durable prefer × atomic apply × round-trip dump × generation floors. No application-debug / repair frontier.

### Metadata
- version: 2
- Task name: nftables-ruleset-generation-cutover
- Title: Nftables Ruleset Seating
- Category: system-administration
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["nftables", "ruleset-fold", "atomic-apply", "base-chain", "generation-gate", "ops-journal"]
- Milestones: 0

## Authoring Brief

### Public contract
Live packet-filter desk under `/etc/nftables.conf` and `/etc/nftables.d/` plus durable prefer/journal under `/var/lib/nft/ops/` must agree. Entrypoint `/app/ops/run_nft_seat.sh` writes `/output/nft-seat.json` with:

- `schema_tag` (string) equal to `nft-seat-v1`
- `tables` — array of `{family, name, generation}`
- `chains` — array of `{table, name, policy, hook, priority}`
- `rules_applied` (integer)
- `seat_ok` (boolean)

Surface `/usr/local/bin/fwhealth` may print `active` while deep seating is wrong. Frozen fixtures under `/app/data/nft/` stay integrity-pinned. The applied ruleset must equal the durable-generation fold of `/etc/nftables.d/` fragments in lexical order with any later abort fragment excluded; base-chain policies must match durable prefer (not the surface decoy); `nft list ruleset` written to `/var/lib/nft/ops/applied.nft` must equal that fold. Two seating runs leave byte-identical `/output/nft-seat.json`.

### Failure topology
Authorities couple: lexical fragment fold (abort override rematerializes unless matching `cutover.ok`), durable generation floors (live decoy floors disagree; under-floor tables stay out of the applied fold), durable prefer for base-chain policies (surface decoy disagrees), atomic replace vs additive append, and round-trip equality of applied dump to the fold. Greening fwhealth or loading any ruleset still fails distant mineral tests when prefer/fold/round-trip disagree.

### Environment shape
- Broken ops helpers under `/app/rim`, `/app/ops`, `/app/bag`, `/app/deck`
- Decoy helpers under `/app/wire` and extra rim/bag scripts
- Live host state under `/etc/nftables.conf`, `/etc/nftables.d`, `/var/lib/nft`
- File-backed `nft` shim under `/usr/local/bin/nft` (no privileged netfilter)
- Immutable fixtures under `/app/data/nft` plus packaging digests
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
- `test_w7_quartz` — `/app/data/nft` packaging digest pin
- `test_j2_onyx` — lexical fold excludes abort; live 90 site-standard
- `test_v5_coral` — base-chain policies match durable prefer (not surface)
- `test_p9_jade` — under-floor table omitted from applied fold / chains
- `test_h8_amber` — applied.nft byte-equals durable fold after normalize
- `test_c1_flint` — matching cutover.ok receipt; gen.live aligned
- `test_r6_slate` — rules_applied exact (blocks additive append inflation)
- `test_u2_mica` — full tables/chains matrix vs durable authority
- `test_m1_opal` — fwhealth may print active; seat_ok still required
- `test_t4_pearl` — second apply keeps rules_applied stable (atomic)

Each test accepts any correct seating end-state; none require oracle-only paths.
Not chain-dependent: each can set up via full entrypoint re-entry.

### Drafting guardrails
Symptoms-only instruction; fair outcomes in `/app/docs` (receipt format,
prefer paths, fold/abort rules). Opaque fix-path symbols from construction
manifest. No intent comments. No golden JSON under environment. Verifier
re-enters seating and derives EXPECTED from durable fixtures.

### Triviality Ledger
- Hand-writing `/output/nft-seat.json` fails because verifier deletes output and re-enters `/app/ops/run_nft_seat.sh` twice.
- Editing only live fragments fails because `helm_w` rematerializes abort.d unless matching `cutover.ok`.
- Using surface prefer fails distant policy cells against durable prefer.
- Including abort fragment or under-floor table greens wrong fold/round-trip.
- Additive `nft -f` without flush inflates `rules_applied` on second pass.
- Leaving `seat_ok` always true fails when round-trip or prefer disagree.

### Per-gate Pitfall Inventory
- RC1: oracle rewrites substantive helper bodies (not delete BUG markers).
- RC2: no broken_/golden_/expected_ names on solver-visible surfaces.
- RC3: tests assert computed policy/generation/rules_applied, not schema alone.
- RC4/RC5: EXPECTED in tests; no golden under environment/.
- RC6: instruction symptoms-only; outcomes not fix recipes.
- RC7: oracle LOC ≥30 substantive lines.
- GX9/GX10: no per-table answer-key recital; no polarity contradiction in one sentence.
- Static: `allow_internet=false`; hashed requirements; PLW1510 `check=`; `.dockerignore`.
- Category: grade live `/etc`/`/var` via bash ops; languages=`["bash"]`; seating framing (not repair/debug).

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
- environment/ops/run_nft_seat.sh
- environment/ops/pin_m.sh
- environment/ops/helm_w.sh
- environment/ops/echo_t.sh
- environment/rim/fold_k.sh
- environment/rim/scan_m.sh
- environment/bag/swap_r.sh
- environment/bag/note_t.sh
- environment/deck/card_w.sh
- environment/wire/knit_p.sh
- environment/cli/nft
- environment/cli/fwhealth
- environment/cli/seatctl
- environment/docs/layout.md
- environment/docs/seating_contract.md
- environment/docs/operator-notes.md
- environment/config/site_standard.conf
- environment/config/surface_prefer.conf
- environment/packaging/nft.sha256
- environment/packaging/README.md
- environment/data/nft/10-core.nft
- environment/data/nft/20-nat.nft
- environment/data/nft/30-mangle.nft
- environment/data/nft/40-raw.nft
- environment/data/roster.list
- environment/data/seed/floors.toml
- environment/data/seed/live_floors.toml
- environment/data/seed/prefer.conf
- environment/data/seed/journal.jsonl
- environment/data/seed/nftables.conf
- environment/data/seed/nftables.d/10-core.nft
- environment/data/seed/nftables.d/20-nat.nft
- environment/data/seed/nftables.d/30-mangle.nft
- environment/data/seed/nftables.d/40-raw.nft
- environment/data/seed/nftables.d/90-local.nft
- environment/data/seed/abort.d/90-local.nft
- environment/data/build_fixtures.sh

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: rim/fold_k.sh
  symbol: fold_k
  kind: function
  signature: fold_k
  purpose: Lexically concatenate nftables.d fragments into fold.nft
- path: ops/pin_m.sh
  symbol: pin_m
  kind: function
  signature: pin_m
  purpose: Rewrite base-chain policy lines from prefer sheet
- path: bag/swap_r.sh
  symbol: swap_r
  kind: function
  signature: swap_r
  purpose: Load fold into nft shim (flush then -f)
- path: ops/echo_t.sh
  symbol: echo_t
  kind: function
  signature: echo_t
  purpose: Dump nft list ruleset into applied.nft
- path: ops/helm_w.sh
  symbol: helm_w
  kind: function
  signature: helm_w
  purpose: Rematerialize abort residue unless durable receipt matches
- path: deck/card_w.sh
  symbol: card_w
  kind: function
  signature: card_w
  purpose: Publish seating ledger JSON from live+durable agreement
```

#### flipping_point_contract

```
locations:
  - id: A
    path: rim/fold_k.sh
    controls_tests: [test_j2_onyx, test_p9_jade, test_u2_mica, test_w7_quartz]
  - id: B
    path: ops/pin_m.sh
    controls_tests: [test_v5_coral, test_u2_mica, test_m1_opal]
  - id: C
    path: bag/swap_r.sh
    controls_tests: [test_r6_slate, test_h8_amber, test_t4_pearl]
  - id: D
    path: ops/helm_w.sh
    controls_tests: [test_c1_flint, test_j2_onyx, test_h8_amber]
  - id: E
    path: deck/card_w.sh
    controls_tests: [test_q3_topaz, test_n4_beryl, test_m1_opal, test_u2_mica]
  - id: F
    path: ops/echo_t.sh
    controls_tests: [test_h8_amber, test_n4_beryl]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: wire/knit_p.sh
  kind: helper
  rhymes_with: fold_k
  non_fix_purpose: Writes operator status crumbs under /var/log/nft
- path: rim/scan_m.sh
  kind: helper
  rhymes_with: pin_m
  non_fix_purpose: Lists table names for fwhealth surface check
- path: bag/note_t.sh
  kind: helper
  rhymes_with: swap_r
  non_fix_purpose: Archives a non-graded fold memo copy
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [packet, filter, desk, ruleset, fragment, fragments, fold, abort, prefer, surface, decoy, generation, cutover, round-trip, roundtrip, nft, tables, chains, policy, hook, priority, seat_ok, fwhealth, fixtures, integrity, operator, docs, layout, schema_tag, family, name, rules_applied, atomic, append, journal, floors, receipt, rematerialize, site-standard, lexical, mode, seal, gen, target, entrypoint]
```
