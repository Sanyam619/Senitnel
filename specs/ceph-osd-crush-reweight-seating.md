### Decision
GO — Attempt 2. Hard system-administration Ceph OSD CRUSH reweight seating with coupled preference-gated rematerialize × packed-map tip resolution × sealed out-journal continuity × hold-window pool placement × canonical idempotent ledger emit. Primary activity is live `/etc/ceph` + `/var/lib/ceph` ops seating end-state, not software repair or debugging.

### Metadata
- version: 2
- Task name: ceph-osd-crush-reweight-seating
- Title: Ceph CRUSH Reweight Seating
- Category: system-administration
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["ceph", "crush-map", "osd-reweight", "placement-group", "out-journal", "generation-gate"]
- Milestones: 0

## Authoring Brief

### Public contract
Live placement materials under `/etc/ceph/` must agree with the durable CRUSH authority under `/var/lib/ceph/ops/` (packed binary map, mirrored as text under `/app/data/crush/`). Entrypoint `/app/ops/run_crush_seat.sh` must produce `/output/crush-seat.json` with:

- `schema_tag` (string) equal to `crush-seat-v1`
- `osds` — array of `{id:int, host:string, weight:number, in:bool, up:bool, generation:int}`
- `pools` — array of `{name:string, size:int, pg_num:int, degraded:bool}`
- `seat_ok` (boolean)

Surface `/usr/local/bin/cephhealth` may print HEALTH_OK while deep seating is wrong. Frozen fixtures under `/app/data/ceph/` and `/app/data/crush/` stay integrity-pinned; the out-journal and hold ledger are sealed records. An OSD is in+up only when its reweight matches the durable CRUSH tip at generation ≥ floor and the sealed out-journal does not leave it out after its last in-epoch. A pool is degraded=false only when placement across the seated set satisfies its size without a held host. Two seating passes must leave byte-identical `/output/crush-seat.json`.

### Failure topology
Authorities couple: a preflight that rematerializes live reweight sheets from a stale surface map on every pass unless the map preference selects durable AND a receipt matching `gen.target` with `mode=seal` exists; durable tip resolution as the newest-generation row per device inside the packed map (live sheets and the surface map disagree; one device's newest tip sits below the generation floor); sealed out-journal continuity where last action by epoch wins (an out followed by a later in is in); hold windows with strict `until_epoch > clock` comparison (an expired hold row must not exclude its host) feeding host-level replica spread that can leave one pool truthfully degraded even after fully correct seating; and a ledger emit that must compute in/up/degraded from state rather than assert them and stay byte-identical across passes. Greening cephhealth or hand-editing `/etc/ceph` still fails distant cells because verifier re-entry re-runs the desk.

### Environment shape
- Broken ops helpers under `/app/ops`, `/app/lane`, `/app/mast`, `/app/deck`
- Decoy helpers beside them doing genuine non-graded work
- Live host state under `/etc/ceph` (reweight sheets, pool declarations with stale state flags) and `/var/lib/ceph/ops` (packed map, surface map, preference, sealed journals, generation floors/targets, state plane)
- Immutable fixtures under `/app/data/ceph` and `/app/data/crush` plus packaging digests
- Outcome docs under `/app/docs`
- Surface health bait `/usr/local/bin/cephhealth` and a decoy map probe tool

### Required artifacts
Standard layout: `instruction.md`, `task.toml`, `output_contract.toml`, `environment/` (≥20 files excl. Docker), `solution/solve.sh`, `tests/{test.sh,test_outputs.py}`, `environment/.dockerignore`, hashed `requirements.txt`.

### Test plan
- `test_k2_agate` — ledger schema, schema_tag literal, types, seat_ok true after re-entry
- `test_d5_basalt` — two seating runs byte-identical, trailing newline
- `test_y8_gneiss` — fixture digest pin + live sealed copies equal pinned mirrors + seat_ok
- `test_r3_pumice` — reweight/up matrix vs durable tips incl. below-floor device up=false
- `test_m6_schist` — journal continuity: out-then-in device in=true; in-then-out device in=false with up=true
- `test_w4_marble` — pool degraded matrix recomputed from seated set
- `test_h9_shale` — active hold excludes its host from placement while its devices stay in+up; expired hold counts
- `test_c1_borax` — receipt matches gen.target/mode; gen.live equals target; live sheets persist across re-entry
- `test_p5_ochre` — generation fields equal newest durable rows; floor polarity comparisons
- `test_t8_umber` — cephhealth still prints HEALTH_OK while deep grading proceeds
- `test_j4_lignite` — full osds array equals EXPECTED derived from pinned fixtures
- `test_e2_galena` — full pools array equals EXPECTED; seat_ok coupling

Each test accepts any correct seating end-state; none require oracle-only paths. Not chain-dependent: each re-enters the full entrypoint.

### Drafting guardrails
Symptoms-only instruction; fair outcome rules (receipt format, last-action journal ordering, strict hold window, computed-vs-reported degraded, floor inclusivity) live in `/app/docs` as desk contract prose, never as a repair checklist. Opaque fix-path symbols from the construction manifest. No intent comments. No golden JSON under environment. Verifier clears `/output`, re-enters seating twice, and derives EXPECTED from digest-pinned fixtures. No repair/debug framing anywhere solver-visible.

### Triviality Ledger
- Hand-writing `/output/crush-seat.json` fails because the verifier deletes the output and re-enters `/app/ops/run_crush_seat.sh` twice.
- Hand-aligning `/etc/ceph/reweight.d` fails because the shipped preflight rematerializes stale surface weights and deletes the receipt on every pass until the preference/receipt gate is implemented.
- Flipping `prefer.toml` alone fails because tip resolution, journal flags, pool math, and emit still disagree with durable authority.
- Hardcoding `in`/`up` true fails the below-floor device and the journal-out device; hardcoding `degraded` false fails the truthfully-degraded archive pool.
- Treating any journal `out` row as permanent exclusion fails the out-then-in device; treating any hold row as active fails the expired-hold host.
- Rewriting the packed map or sealed journals to match wrong live edits fails the digest-pin and sealed-copy equality tests.

### Per-gate Pitfall Inventory
- RC1: oracle rewrites substantive helper bodies with new multi-authority logic (no marker deletion).
- RC2: no broken_/golden_/expected_ tokens on solver-visible surfaces; opaque helper names.
- RC3: tests assert computed weight/in/up/generation/degraded values recomputed from fixtures, never schema-only.
- RC4/RC5: EXPECTED derived in test code from digest-pinned `/app/data` fixtures; live `/var/lib` copies asserted equal to pins so tampering fails.
- RC6: instruction symptoms-only; acceptance rules are outcomes in docs, not fix recipes.
- RC7: oracle ≥ 200 substantive LOC across five helper bodies.
- GX9: no per-device or per-pool expected-value recital in instruction; observations only.
- GX10: in/up and degraded polarities stated in separate sentences with unambiguous scope.
- Static: `allow_internet=false`; hashed requirements + `--require-hashes`; explicit `check=` on every `subprocess.run`; `.dockerignore` shipped; LF endings; pinned digests/apt.
- Category: grade live `/etc`/`/var` end-state via bash ops helpers; languages `["bash"]`; storage-ops tags; no repair/debug aura.

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
- environment/ops/run_crush_seat.sh
- environment/ops/kelp_v.sh
- environment/ops/gorse_t.sh
- environment/lane/moss_q.sh
- environment/lane/brome_j.sh
- environment/mast/fern_h.sh
- environment/mast/vetch_r.sh
- environment/deck/tarn_e.sh
- environment/deck/sedge_w.sh
- environment/tools/cephhealth
- environment/tools/mapprobe
- environment/docs/layout.md
- environment/docs/seating_contract.md
- environment/docs/operator-notes.md
- environment/packaging/README.md
- environment/packaging/fixtures.sha256
- environment/data/crush/crush_map.txt
- environment/data/ceph/osds/osd.0.toml
- environment/data/ceph/osds/osd.1.toml
- environment/data/ceph/osds/osd.2.toml
- environment/data/ceph/osds/osd.3.toml
- environment/data/ceph/osds/osd.4.toml
- environment/data/ceph/osds/osd.5.toml
- environment/data/ceph/osds/osd.6.toml
- environment/data/ceph/osds/osd.7.toml
- environment/data/ceph/pools/vault-meta.toml
- environment/data/ceph/pools/vault-data.toml
- environment/data/ceph/pools/archive-cold.toml
- environment/data/ceph/out_journal.jsonl
- environment/data/ceph/holds.jsonl
- environment/data/ceph/epochs.toml
- environment/data/seed/ceph.conf
- environment/data/seed/prefer.toml
- environment/data/seed/surface.map
- environment/data/seed/reweight.d/osd.0.conf
- environment/data/seed/reweight.d/osd.1.conf
- environment/data/seed/reweight.d/osd.2.conf
- environment/data/seed/reweight.d/osd.3.conf
- environment/data/seed/reweight.d/osd.4.conf
- environment/data/seed/reweight.d/osd.5.conf
- environment/data/seed/reweight.d/osd.6.conf
- environment/data/seed/reweight.d/osd.7.conf
- environment/data/seed/pools.d/10-vault.conf
- environment/data/seed/pools.d/20-archive.conf
- environment/data/build_fixtures.sh

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: ops/kelp_v.sh
  symbol: kelp_v
  kind: function
  signature: kelp_v
  purpose: Gate the live-sheet rematerialize pass on the durable preference and a matching apply receipt
- path: ops/gorse_t.sh
  symbol: gorse_t
  kind: function
  signature: gorse_t
  purpose: Decode the packed durable map, resolve the newest row per device, align live sheets and write the apply receipt
- path: lane/moss_q.sh
  symbol: moss_q
  kind: function
  signature: moss_q
  purpose: Materialize per-device exclusion flags from the sealed record stream using last-action ordering
- path: mast/fern_h.sh
  symbol: fern_h
  kind: function
  signature: fern_h
  purpose: Compute per-group spread marks from the seated set minus active window entries
- path: deck/tarn_e.sh
  symbol: tarn_e
  kind: function
  signature: tarn_e
  purpose: Publish the canonical output document from state files with full agreement conjunction
```

#### flipping_point_contract

```
locations:
  - id: A
    path: ops/kelp_v.sh
    controls_tests: [test_d5_basalt, test_r3_pumice, test_c1_borax]
  - id: B
    path: ops/gorse_t.sh
    controls_tests: [test_r3_pumice, test_c1_borax, test_p5_ochre, test_j4_lignite]
  - id: C
    path: lane/moss_q.sh
    controls_tests: [test_m6_schist, test_j4_lignite]
  - id: D
    path: mast/fern_h.sh
    controls_tests: [test_w4_marble, test_h9_shale, test_e2_galena]
  - id: E
    path: deck/tarn_e.sh
    controls_tests: [test_k2_agate, test_d5_basalt, test_y8_gneiss, test_t8_umber, test_e2_galena]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: lane/brome_j.sh
  kind: helper
  rhymes_with: moss_q
  non_fix_purpose: Prints an inventory of live sheet filenames to an operator note under /var/log/ceph/
- path: mast/vetch_r.sh
  kind: helper
  rhymes_with: fern_h
  non_fix_purpose: Appends a desk activity note under /var/log/ceph/ for shift handover
- path: deck/sedge_w.sh
  kind: helper
  rhymes_with: tarn_e
  non_fix_purpose: Touches a probe stamp under /var/run/ceph/ for the surface monitor
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [ceph, crush, osd, osds, reweight, seat, seating, pool, pools, degraded, generation, journal, host, hosts, hold, held, weight, placement, tip, map, mirror, floor, epoch, ledger, authority, fixtures, schema, desk, materials, device, health]
```
