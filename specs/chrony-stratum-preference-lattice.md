### Decision
GO — Attempt 1. System-administration chrony/timesync seating via live `/etc` + `/var` ops: preference lattice rematerialize, lexical timesync drop-in fold, hold×roster×stratum-band selection, false-green `timehealth`, durable offset budget. Configure/seat framing (not repair/debug). Languages bash only.

### Metadata
- version: 2
- Task name: chrony-stratum-preference-lattice
- Title: Chrony Stratum Preference Lattice
- Category: system-administration
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["chrony", "stratum", "time-seating", "preference-lattice", "dropin-policy", "hold-window"]
- Milestones: 0

## Authoring Brief

### Public contract
Seat the time desk so `/app/ops/run_time_seat.sh` emits `/output/time-seat.json` with:
- `schema_tag` (string)
- `sources` (array of `{name, stratum, selected, hold}`)
- `preference` (string: `live` | `durable` | `authority`)
- `sync_ok` (boolean)
- `offset_bound_ms` (number)

Live materials sit under `/etc/chrony/`, `/etc/systemd/timesyncd.conf.d/`, and `/var/lib/chrony/`. Durable preference lives under `/var/lib/time/ops/prefer.toml`. A source is selected only when it is on the durable roster, its stratum is inside the published band in `/app/docs/time_bands.md`, and it is not held. `/usr/local/bin/timehealth` may print synchronized while `sync_ok` is false. Do not rewrite frozen samples under `/app/data/sources/`. Two seating runs must yield byte-identical output.

### Failure topology
Preference mode still `live`/`surface` rematerializes chrony sources and timesync drop-ins from permanently wrong surface seeds, undoing naive edits. Lexical drop-in fold still prefers a decoy NTP peer. Hold markers are ignored or omit rows instead of reporting `hold:true` with `selected:false`. Emit path trusts `timehealth` for `sync_ok` / `offset_bound_ms` and copies a surface `schema_tag`. Partial fixes leave distant cells red: durable prefer without band×hold selection still admits out-of-band or held peers; correct JSON alone fails live chrony / re-entry.

### Environment shape
- `/app/ops/` — seating entrypoint plus opaque helpers (prefer gate, drop-in fold, hold apply, chrony bind, emit).
- `/app/rim/` — offset-budget helper.
- `/app/decoy/` — health/skims that rhyme with fix symbols but only drive surface checks.
- `/app/docs/` — bands, seating outcomes, layout (no fix recipe).
- `/app/config/` + seeded live trees materialized to `/etc` and `/var`.
- `/app/data/sources/` — frozen sample digests.
- `/usr/local/bin/timehealth` — false-green surface shim.

### Required artifacts
Standard layout: `instruction.md`, `task.toml`, `output_contract.toml`, `environment/` (≥20 files excl. Docker), `solution/solve.sh`, `tests/{test.sh,test_outputs.py}`. Hashed `requirements.txt`. `.dockerignore`.

### Test plan
1. `test_q3_opal` — required keys/types present after seating.
2. `test_n7_topaz` — preference is `durable` or `authority`.
3. `test_k4_beryl` — selected set equals roster ∩ band ∩ ¬hold (exact).
4. `test_m2_garnet` — held roster peers appear with `hold:true`, `selected:false`.
5. `test_r6_quartz` — `sync_ok` true only when exactly one durable-selected live peer is seated.
6. `test_w8_zircon` — `offset_bound_ms` equals durable budget for the selected peer (not timehealth).
7. `test_j1_jasper` — `schema_tag` matches durable authority tag.
8. `test_p5_peridot` — `/etc/chrony/sources.d/` matches the selected peer only.
9. `test_v9_spinel` — folded timesync NTP equals durable peer, not decoy.
10. `test_t2_tourmaline` — two seats → byte-identical JSON.
11. `test_h5_hematite` — wipe `/output`, re-run stock entrypoint → same outcomes.
12. `test_u4_onyx` — `/app/data/sources/` digests unchanged.
13. `test_y6_amber` — forcing timehealth-green alone does not satisfy sync/selection cells.
14. `test_c8_citrine` — out-of-band roster peer never `selected:true`.

Multiple ops sequences OK if outcomes hold. Re-entry/idempotence assume a prior successful seat.

### Drafting guardrails
Symptoms-only instruction; configure/seat framing (no repair/debug). Opaque fix-path symbols. No answer-key selected tallies or closed-form offset algebra in instruction. Document band/outcomes in `/app/docs/`. Prefer rematerialize must fire from seating entrypoint. No greppable always-wrong three-stub polarity as the whole frontier — couple prefer×fold×hold×emit.

### Triviality Ledger
- Editing only chrony.conf fails because prefer rematerialize restores surface seeds on next seat.
- Hand-writing `/output/time-seat.json` fails re-entry wipe + stock entrypoint.
- Trusting timehealth fails `sync_ok` / offset budget cells.
- Flipping prefer alone without fold×hold×band still admits decoy NTP / held / out-of-band peers.
- Omitting held rows fails hold-row tests; selecting held peers fails selection matrix.

### Per-gate Pitfall Inventory
- RC1: oracle adds substantive ops logic, not delete-only.
- RC2: no broken_/golden_/fix_me_ names.
- RC3: tests assert domain selection/offset/fold, not existence alone.
- RC4/RC5: EXPECTED embedded in tests; no golden JSON under environment/.
- RC6: symptoms-only instruction; bands discovered in docs.
- RC7: solve.sh ≥30 substantive LOC.
- GX9/GX10: no per-scenario answer recital or polarity contradiction.
- Static: `allow_internet=false`, hashed pip, PLW1510 `check=`, `.dockerignore`, category `system-administration`, languages `bash`.

### Initial Draft Commitments
- `instruction.md`
- `task.toml`
- `output_contract.toml`
- `environment/Dockerfile`
- `environment/.dockerignore`
- `environment/requirements.txt`
- `environment/ops/run_time_seat.sh`
- `environment/ops/axle_p.sh`
- `environment/ops/knit_w.sh`
- `environment/ops/pull_m.sh`
- `environment/ops/bind_v.sh`
- `environment/ops/emit_q.sh`
- `environment/rim/mark_t.sh`
- `environment/decoy/skim_z.sh`
- `environment/decoy/fold_scan.sh`
- `environment/docs/time_bands.md`
- `environment/docs/seating_contract.md`
- `environment/docs/layout.md`
- `environment/config/prefer.surface.toml`
- `environment/config/authority.toml`
- `environment/config/roster.toml`
- `environment/config/holds.toml`
- `environment/config/offsets.toml`
- `environment/config/timesync.d/10-core.conf`
- `environment/config/timesync.d/40-lab.conf`
- `environment/config/timesync.d/90-local.conf`
- `environment/config/chrony/chrony.conf`
- `environment/config/chrony/sources.d/alpha.sources`
- `environment/config/chrony/sources.d/beta.sources`
- `environment/config/chrony/sources.d/gamma.sources`
- `environment/config/chrony/sources.d/delta.sources`
- `environment/config/chrony/sources.d/epsilon.sources`
- `environment/config/surface/sources.d/alpha.sources`
- `environment/config/surface/sources.d/beta.sources`
- `environment/config/surface/sources.d/gamma.sources`
- `environment/config/surface/sources.d/delta.sources`
- `environment/config/surface/sources.d/epsilon.sources`
- `environment/config/surface/timesync.d/10-core.conf`
- `environment/config/surface/timesync.d/40-lab.conf`
- `environment/config/surface/timesync.d/90-local.conf`
- `environment/data/sources/alpha.json`
- `environment/data/sources/beta.json`
- `environment/data/sources/gamma.json`
- `environment/data/sources/delta.json`
- `environment/data/sources/epsilon.json`
- `environment/data/sources.sha256`
- `environment/tools/timehealth`
- `environment/packaging/README.md`
- `solution/solve.sh`
- `tests/test.sh`
- `tests/test_outputs.py`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table
```
- path: ops/axle_p.sh
  symbol: axle_p
  kind: function
  signature: axle_p()
  purpose: prefer-gate rematerialize of live chrony/timesync from surface seeds
- path: ops/knit_w.sh
  symbol: knit_w
  kind: function
  signature: knit_w()
  purpose: lexical fold of timesyncd drop-ins into effective NTP
- path: ops/pull_m.sh
  symbol: pull_m
  kind: function
  signature: pull_m()
  purpose: apply hold window into seating state
- path: ops/bind_v.sh
  symbol: bind_v
  kind: function
  signature: bind_v()
  purpose: write live chrony sources from roster×band×hold
- path: ops/emit_q.sh
  symbol: emit_q
  kind: function
  signature: emit_q()
  purpose: emit /output/time-seat.json from durable state
- path: rim/mark_t.sh
  symbol: mark_t
  kind: function
  signature: mark_t()
  purpose: derive offset_bound_ms from durable budgets for seated peer
```

#### flipping_point_contract
```
locations:
  - id: A
    path: ops/axle_p.sh
    controls_tests: [test_n7_topaz, test_j1_jasper, test_h5_hematite]
  - id: B
    path: ops/knit_w.sh
    controls_tests: [test_v9_spinel, test_y6_amber]
  - id: C
    path: ops/pull_m.sh
    controls_tests: [test_m2_garnet, test_c8_citrine]
  - id: D
    path: ops/bind_v.sh
    controls_tests: [test_k4_beryl, test_p5_peridot, test_r6_quartz]
  - id: E
    path: ops/emit_q.sh
    controls_tests: [test_q3_opal, test_t2_tourmaline, test_u4_onyx]
  - id: F
    path: rim/mark_t.sh
    controls_tests: [test_w8_zircon]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest
```
- path: decoy/skim_z.sh
  kind: helper
  rhymes_with: emit_q
  non_fix_purpose: wraps timehealth surface smoke; never writes seating JSON
- path: decoy/fold_scan.sh
  kind: helper
  rhymes_with: knit_w
  non_fix_purpose: prints drop-in filenames for operators; does not fold NTP
```

#### code_forbidden_tokens
```
code_forbidden_tokens: [desk, time, seating, entrypoint, report, schema_tag, sources, stratum, selected, hold, preference, live, durable, authority, sync_ok, offset_bound_ms, chrony, timesync, materials, roster, band, published, frozen, samples, synchronized, timehealth, dropin, offset, bound, sync, source, name, peer, ntp]
```
