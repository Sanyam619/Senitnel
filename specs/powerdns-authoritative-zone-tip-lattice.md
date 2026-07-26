### Decision
GO — Attempt 1. System-administration PowerDNS authoritative zone seating desk: live `/etc/powerdns` + durable sealed zone-tip journal (superseded same-gen revision + incomplete later bait) × backend store registry with retirement ledger (newest row retired; live sqlite decoy) × pdns.d fold abort × record-hold honor ledger × receipt-gated abort rematerialize × prefer-gated surface rematerialize. No repair/debug framing; bash ops only; distinct from squid ICP peer seating (store registry retirements + record holds replace peer journal revoke + ACL array) and from DNSSEC trust and Kea DHCP tasks.

### Metadata
- version: 2
- Task name: powerdns-authoritative-zone-tip-lattice
- Title: PowerDNS Zone Seating
- Category: system-administration
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["powerdns", "zone-serial", "backend-prefer", "pdns-fold", "generation-gate", "ops-journal"]
- Milestones: 0

## Authoring Brief

### Public contract
Seat the authoritative DNS desk so `/app/ops/run_pdns_seat.sh` writes `/output/pdns-seat.json` with `schema_tag` (string), `zones` (array of `{name, serial, backend, generation, published}`), `records` (array of `{zone, name, type, content, honored}`), and `seat_ok` (boolean). Live config under `/etc/powerdns/` and `/etc/powerdns/pdns.d/`; durable prefer + zone journal + store registry + holds under `/var/lib/powerdns/ops/`. A zone is published only when its live serial matches the durable journal tip at generation ≥ floor, its live store sheet matches the prefer-selected backing store (not the live sqlite decoy), and the pdns.d fold does not abort it. Records that diverge from the sealed tip carry `honored=false`; held records diverge by design on a correct seat. `/usr/local/bin/pdnshealth` may print serving while `seat_ok` is false. Frozen fixtures under `/app/data/pdns/` stay intact. Verifier re-invokes seating after wiping `/output`; two runs byte-identical; hand-authored JSON fails.

### Failure topology
Surface health greening config presence while durable seating fails; live zone sheets, serial sheets, and store sheets carry stale/decoy values; abort residue rematerializes into live pdns.d unless a matching cutover receipt exists; surface tip/zone-sheet materials rematerialize over naive SOA/serial edits while preference stays live; the newest store registry row is retired so newest-any selection lands on the sqlite decoy; a superseded same-generation journal revision poisons first-match readers; an incomplete later generation baits eager appliers; record holds force mixed honored polarity so flip-everything-true reward hacks fail. Couplings: receipt × tip apply × fold × store resolve × record honor × surface gate — fixing one locus alone fails distant cells.

### Environment shape
Ops entrypoint chain across `ops/`, `rig/`, `span/`, `wire/`, `deck/`, `bag/`; durable zone journal + store registry + retirement ledger + holds + floors + abort package; live pdns.conf + pdns.d drop-ins + zones.d record/store sheets + serial sheets; site-standard sheet; frozen zone fixtures with apex data; surface bait `pdnshealth`; packaging digest pin.

### Required artifacts
Standard layout: `instruction.md`, `task.toml`, `output_contract.toml`, `environment/` (≥20 files), `solution/solve.sh`, `tests/{test.sh,test_outputs.py}`.

### Test plan
- Schema + seat_ok + published polarity after reseat
- Byte-identical double seat + gen.live
- Frozen fixture apex/durable alignment
- Superseded same-gen journal revision (latest-batch rule)
- Incomplete later gen not applied; bind gen settles on target
- Store registry retirement resolution (not the sqlite decoy)
- Generation ≥ durable floor polarity (live floors decoys)
- pdns.d fold abort union; site-standard fold end-state
- Abort package forensic vs live site-standard tokens
- Cutover receipt semantics + poisoned-receipt re-entry
- Record holds mixed honored polarity with seat_ok true
- Live sheets carry tip serials/contents/stores
- Surface serving bait ≠ seat_ok
- State wipe + /output wipe re-entry reconstitutes matrix
- Prefer flip re-entry poisons then recovers
- Full zones+records matrix equality vs derived EXPECTED

### Drafting guardrails
Symptoms/outcomes in instruction; contract detail in `/app/docs/`; opaque helper names; no intent comments on fix path; EXPECTED derived in tests from durable journal/registry/holds/floors; no repair/debug vocabulary in instruction opener; no correct resolution logic beside broken helpers (emitter checks recorded state, never re-resolves journal or registry).

### Triviality Ledger
- Serving print alone → fails seat_ok / matrix (surface bait)
- Bumping live serials by hand → surface rematerialize rewrites them while prefer is live/bind stale
- Applying newest journal batch → incomplete gen-9 bait fails tip cells
- First-match gen-7 batch → superseded revision serials/contents fail 4/5 zones
- Newest registry row → retired sqlite decoy fails backend cells even with serials right
- Marking every record honored → held records must stay divergent; flip-all fails matrix
- Editing live pdns.d only → abort residue rematerializes unless receipt gen=target+mode=seal
- Deleting live 90-local to "suppress" abort → live drop-in must remain with site tokens

### Per-gate Pitfall Inventory
- RC1/RC7: oracle rewrites 5 helper bodies + prefer mode with substantive logic (≥120 LOC)
- RC2/CR7: opaque helper names (crib_j, lath_p, gaff_s, moor_w, keel_x); mineral test names
- RC3: behavioral reseat + derived EXPECTED from durable ledgers, not schema-only
- RC4/RC5: no golden outputs under environment/; digests pin only frozen inputs
- RC6: symptoms instruction; outcomes in docs; no numbered fix checklist
- GX9/GX10: no exact serial/store recital in instruction; polarity in separate sentences
- PLW1510/PLR0124: explicit check= on subprocess.run; no v==v idioms
- Category: live `/etc`/`/var` seating, languages=bash, no SE repair aura, no cargo/make

### Initial Draft Commitments
- instruction.md, task.toml, output_contract.toml
- environment/{Dockerfile,.dockerignore,requirements.txt}
- environment/docs/{layout.md,zone_contract.md,operator-notes.md}
- environment/config/{site_standard.conf,prefer.surface.toml}
- environment/ops/{run_pdns_seat.sh,crib_j.sh,lath_p.sh}
- environment/rig/{vane_t.sh,scan_y.sh}
- environment/span/moor_w.sh
- environment/wire/{keel_x.sh,lace_n.sh}
- environment/deck/flue_d.sh
- environment/bag/note_g.sh
- environment/tools/{pdnshealth,zoneprobe}
- environment/packaging/{README.md,zones.sha256}
- environment/data/{zone.roster,build_fixtures.sh,pdns/*.toml,seed/**}
- solution/solve.sh
- tests/{test.sh,test_outputs.py}

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table
```
- path: ops/crib_j.sh
  symbol: crib_j
  kind: function
  signature: crib_j()
  purpose: receipt-gated abort package copy into live pdns.d
- path: ops/lath_p.sh
  symbol: lath_p
  kind: function
  signature: lath_p()
  purpose: sealed journal batch resolve, tip state, gen.live, bind accept, site-standard install, cutover receipt
- path: rig/gaff_s.sh
  symbol: gaff_s
  kind: function
  signature: gaff_s()
  purpose: registry row selection minus retirement ledger into store.sel
- path: span/moor_w.sh
  symbol: moor_w
  kind: function
  signature: moor_w()
  purpose: live sheet/serial/store writes, publish and honor state
- path: wire/keel_x.sh
  symbol: keel_x
  kind: function
  signature: keel_x()
  purpose: surface material rematerialize gated on preference + bind
```

#### flipping_point_contract
```
locations:
  - id: A
    path: ops/crib_j.sh
    controls_tests: [test_c6_shale, test_w1_borax]
  - id: B
    path: ops/lath_p.sh
    controls_tests: [test_v9_chert, test_m3_pumice, test_r7_basalt]
  - id: C
    path: rig/gaff_s.sh
    controls_tests: [test_j6_schist]
  - id: D
    path: span/moor_w.sh
    controls_tests: [test_h9_norite, test_e2_talc, test_t8_gneiss]
  - id: E
    path: wire/keel_x.sh
    controls_tests: [test_y7_umber, test_u4_gabbro]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest
```
- path: rig/scan_y.sh
  kind: helper
  rhymes_with: gaff_s
  non_fix_purpose: lists pdns.d filenames only
- path: wire/lace_n.sh
  kind: helper
  rhymes_with: keel_x
  non_fix_purpose: touches probe.stamp
- path: bag/note_g.sh
  kind: helper
  rhymes_with: moor_w
  non_fix_purpose: appends operator note to log
```

#### code_forbidden_tokens
```
code_forbidden_tokens: [powerdns, dns, zone, serial, backend, store, sqlite, journal, tip, generation, floor, record, hold, honored, published, prefer, durable, live, surface, seat, abort, cutover, receipt, health, fixture, roster, fold, schema, ledger, registry, retirement]
```
