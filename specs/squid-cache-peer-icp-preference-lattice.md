### Decision
GO — Attempt 1. System-administration Squid ICP peer seating desk: live `/etc/squid` + durable prefer tip × peer-journal revoke × ACL first-match abort × generation floors. No repair/debug framing; bash ops only; distinct from HAProxy drain and chrony stratum (sealed tip + revoke journal + Squid-native ACL abort).

### Metadata
- version: 2
- Task name: squid-cache-peer-icp-preference-lattice
- Title: Squid ICP Peer Seating
- Category: system-administration
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["squid", "cache-peer", "icp", "acl-fold", "peer-journal", "generation-gate"]
- Milestones: 0

## Authoring Brief

### Public contract
Seat the forward-proxy cache desk so `/app/ops/run_squid_seat.sh` writes `/output/squid-seat.json` with `schema_tag` (string), `peers` (array of `{name, host, type, weight, generation, selected}`), `acls` (array of `{name, matched}`), and `seat_ok` (boolean). Live config under `/etc/squid/` and `/etc/squid/conf.d/`; durable prefer + peer journal under `/var/lib/squid/ops/`. A peer is selected only when its type/weight match the durable prefer tip at generation ≥ floor, it is present in the sealed peer journal (not revoked), and conf.d ACL fold does not abort it. `/usr/local/bin/squidhealth` may print ready while `seat_ok` is false. Frozen fixtures under `/app/data/squid/` stay intact. Verifier re-invokes seating; two runs byte-identical; hand-authored JSON fails.

### Failure topology
Surface health greening TCP reachability while durable selection fails; live peer sheets carry sibling/parent and weight decoys; abort residue rematerializes revoked peers into live conf.d unless a matching cutover receipt exists; ACL fold first-match abort kills otherwise tip-eligible peers; below-floor generations and incomplete later tips must not seat. Couplings: rematerialize × tip resolve × journal × ACL × emit self-audit — fixing one locus alone fails distant cells.

### Environment shape
Ops entrypoint chain across `ops/`, `rim/`, `bag/`, `wire/`, `deck/`; durable prefer tip journal + peer revoke journal + floors + abort package; live squid.conf + conf.d ACL drop-ins + peers.d; site-standard sheet; frozen peer fixtures; surface bait `squidhealth`; packaging digest pin.

### Required artifacts
Standard layout: `instruction.md`, `task.toml`, `output_contract.toml`, `environment/` (≥20 files), `solution/solve.sh`, `tests/{test.sh,test_outputs.py}`.

### Test plan
- Schema + seat_ok after reseat
- Byte-identical double seat
- Fixture integrity pin
- Prefer tip sealed/complete over incomplete later tip
- Generation ≥ floor polarity
- Journal revoke excludes peer
- ACL first-match abort
- Abort forensic vs live site-standard + cutover receipt
- Parent/sibling type match vs live decoy
- Full peer matrix + selected set
- Surface ready ≠ seat_ok
- Novel peer inject / re-entry

### Drafting guardrails
Symptoms/outcomes in instruction; contract detail in `/app/docs/`; opaque helper names; no intent comments on fix path; EXPECTED derived in tests; no repair/debug vocabulary in instruction opener.

### Triviality Ledger
- TCP-ready alone → fails seat_ok / selected matrix (surface bait)
- Seating “fast” high-weight incomplete tip → fails sealed-tip and ACL cells
- Editing live conf only → rematerialize restores abort unless receipt+tip cutover
- First-file ACL fold → wrong abort set
- Ignoring revoke → south still selected
- Live floors / sibling decoy for north → type/weight mismatch fails emit audit

### Per-gate Pitfall Inventory
- RC1/RC7: oracle rewrites ≥6 helper bodies with substantive logic (≥80 LOC)
- RC2/CR7: opaque helper names; mineral test names
- RC3: behavioral reseat + derived EXPECTED, not schema-only
- RC4/RC5: no golden under environment/; pin digests only
- RC6: symptoms instruction; outcomes in docs
- GX9/GX10: no answer triples or polarity contradictions in instruction
- PLW1510: explicit check= on subprocess.run
- Category: live `/etc`/`/var` seating, languages=bash, no SE repair aura

### Initial Draft Commitments
- instruction.md, task.toml, output_contract.toml
- environment/{Dockerfile,.dockerignore,requirements.txt}
- environment/docs/{layout.md,seating_contract.md,operator-notes.md}
- environment/config/site_standard.conf
- environment/ops/{run_squid_seat.sh,helm_r.sh,axle_n.sh}
- environment/rim/{mesh_k.sh,scan_t.sh}
- environment/bag/{skim_p.sh,note_u.sh}
- environment/wire/{sock_v.sh,knit_q.sh}
- environment/deck/emit_m.sh
- environment/tools/{squidhealth,sockprobe}
- environment/packaging/{README.md,peers.sha256}
- environment/data/{roster.list,build_fixtures.sh,squid/*.toml,seed/**}
- solution/solve.sh
- tests/{test.sh,test_outputs.py}

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table
```
- path: ops/helm_r.sh
  symbol: helm_r
  kind: function
  signature: helm_r()
  purpose: receipt-gated abort package copy into live conf.d
- path: ops/axle_n.sh
  symbol: axle_n
  kind: function
  signature: axle_n()
  purpose: sealed prefer tip resolve, gen.live, site-standard install, cutover receipt
- path: rim/mesh_k.sh
  symbol: mesh_k
  kind: function
  signature: mesh_k()
  purpose: lexical conf.d ACL fold with first-match abort set
- path: bag/skim_p.sh
  symbol: skim_p
  kind: function
  signature: skim_p()
  purpose: sealed peer journal presence minus revoke
- path: wire/sock_v.sh
  symbol: sock_v
  kind: function
  signature: sock_v()
  purpose: apply tip type/weight and selection flags to live peers.d
- path: deck/emit_m.sh
  symbol: emit_m
  kind: function
  signature: emit_m()
  purpose: emit squid-seat.json with self-audit seat_ok
```

#### flipping_point_contract
```
locations:
  - id: A
    path: ops/helm_r.sh
    controls_tests: [test_h8_amber, test_c1_flint]
  - id: B
    path: ops/axle_n.sh
    controls_tests: [test_v5_coral, test_c1_flint, test_n4_beryl]
  - id: C
    path: rim/mesh_k.sh
    controls_tests: [test_r6_slate, test_j2_onyx]
  - id: D
    path: bag/skim_p.sh
    controls_tests: [test_p9_jade, test_u2_mica]
  - id: E
    path: wire/sock_v.sh
    controls_tests: [test_m1_opal, test_k5_garnet]
  - id: F
    path: deck/emit_m.sh
    controls_tests: [test_q3_topaz, test_t4_pearl, test_u2_mica]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest
```
- path: rim/scan_t.sh
  kind: helper
  rhymes_with: mesh_k
  non_fix_purpose: lists conf.d filenames only
- path: bag/note_u.sh
  kind: helper
  rhymes_with: skim_p
  non_fix_purpose: appends operator note to log
- path: wire/knit_q.sh
  kind: helper
  rhymes_with: sock_v
  non_fix_purpose: touches probe.stamp
```

#### code_forbidden_tokens
```
code_forbidden_tokens: [squid, peer, cache, icp, preference, lattice, tip, journal, acl, fold, generation, floor, weight, type, parent, sibling, revoke, health, durable, live, conf, selected, schema, seat, abort, cutover, rematerialize, prefer, host, matched, roster, fixture]
```
