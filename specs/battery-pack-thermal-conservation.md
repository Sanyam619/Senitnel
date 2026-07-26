### Decision
GO — Attempt 3. Scientific pack-thermal desk (taxonomy `scientific-computing`, languages python/bash): operate installed FV desk for conservation×hotspot bands under ship/fleet; opaque contact/reduction/dt loci with plausible-wrong physics (not empty polarity stubs); policy overlay rematerialize vs sealed cutover; surface thermalsurf non-graded. No repair/debug primary activity.

### Metadata
- version: 2
- Task name: battery-pack-thermal-conservation
- Title: Battery Pack Thermal Conservation
- Category: scientific-computing
- Languages: ["python", "bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["thermal", "battery", "conservation", "hotspot", "residuals"]
- Milestones: 0

## Authoring Brief

### Public contract

Operate the lithium-ion pack thermal evaluation desk under `/app` so rebuilt solves meet energy-conservation and hotspot agreement bands in `/app/docs/thermal_bands.md` on frozen fixtures under `/app/data/packs/` (ledger-protected).

Emit `/output/thermal-conserve-report.json` only via `/app/ops/run_thermal_report.sh --all-profiles` after rebuild. Schema: `status` ("ok"), `eval_sha`, `profiles` (array of `{profile_id, energy_rel_err, hotspot_rel_err, max_dT_K, contact_model, reduction_order, dt_policy}`), `run_stamp`.

Ship and fleet profiles under `/app/config/profiles/` declare required tokens and band caps published in thermal_bands.md. Both profiles must pass. `/app/bin/thermalsurf` is non-graded. Verifier rebuilds from `/app`, re-runs entrypoint, requires byte-identical double run. Do not alter fixtures.

### Failure topology

Contact interface conductance, canceling-flux reduction, and timestep policy disagree with profile declarations. Surface dashboard reports ok while deep energy_rel_err / hotspot_rel_err exceed bands. Fixing one locus leaves the other profile or residual axis failing.

### Environment shape

Python FV thermal solver with opaque `op_a`/`op_b`/`op_c` under solver roots, core stepper, decoy skim, ship/fleet profiles, pack fixtures + ledger, bands doc, layout notes, thermalsurf, report harness, rebuild script.

### Required artifacts

Standard task layout; ≥20 env files; oracle patches three opaque modules with substantive physics (≥30 LOC); no golden report under environment/.

### Test plan

- `test_k3_zircon` — report schema and both profile_ids present
- `test_v4_jade` — ship energy_rel_err within band
- `test_p2_garnet` — hotspot_rel_err and max_dT_K within bands for both profiles
- `test_r1_onyx` — contact_model/reduction_order/dt_policy match profile tokens
- `test_w9_flint` — byte-identical double run
- `test_q7_topaz` — fleet energy_rel_err within band
- `test_t6_amber` — thermalsurf ok while broken baseline would fail deep (post-oracle deep ok; assert surf ≠ sole authority by requiring deep fields)
- `test_m8_obsidian` — verifier-owned rebuild path + report re-entry

### Drafting guardrails

Symptoms-only instruction; no conservation algebra paste in docs; opaque symbols; EXPECTED bands only in tests/profiles; thermalsurf false-green on broken baseline.

### Triviality Ledger

- Editing only contact token fails energy under wrong reduction.
- Correct reduction with wrong contact fails hotspot/fleet cells.
- Matching tokens without conservation bodies fails residual bands.
- Hand-written report fails rebuild re-entry.

### Per-gate Pitfall Inventory

- RC1/RC7: substantive patches to three modules, not delete-bug.
- RC3: assert residual numbers and tokens, not existence.
- RC5: no golden report in env.
- RC6: no formula dump in instruction.
- CR1/CR2/CR7: manifest symbols; concentration ≤0.5; opaque names.
- Category: lead with numerical bands, not repair language.

### Initial Draft Commitments

- `tasks/battery-pack-thermal-conservation/task.toml`
- `tasks/battery-pack-thermal-conservation/instruction.md`
- `tasks/battery-pack-thermal-conservation/output_contract.toml`
- `tasks/battery-pack-thermal-conservation/tests/test.sh`
- `tasks/battery-pack-thermal-conservation/tests/test_outputs.py`
- `tasks/battery-pack-thermal-conservation/solution/solve.sh`
- `tasks/battery-pack-thermal-conservation/environment/Dockerfile`
- `tasks/battery-pack-thermal-conservation/environment/.dockerignore`
- `tasks/battery-pack-thermal-conservation/environment/docs/thermal_bands.md`
- `tasks/battery-pack-thermal-conservation/environment/docs/layout_notes.md`
- `tasks/battery-pack-thermal-conservation/environment/config/profiles/ship.toml`
- `tasks/battery-pack-thermal-conservation/environment/config/profiles/fleet.toml`
- `tasks/battery-pack-thermal-conservation/environment/ops/run_thermal_report.sh`
- `tasks/battery-pack-thermal-conservation/environment/ops/rebuild.sh`
- `tasks/battery-pack-thermal-conservation/environment/bin/thermalsurf`
- `tasks/battery-pack-thermal-conservation/environment/solver/core/step.py`
- `tasks/battery-pack-thermal-conservation/environment/knit_x/op_a.py`
- `tasks/battery-pack-thermal-conservation/environment/fold_y/op_b.py`
- `tasks/battery-pack-thermal-conservation/environment/slot_z/op_c.py`
- `tasks/battery-pack-thermal-conservation/environment/solver/decoy/skim_w.py`
- `tasks/battery-pack-thermal-conservation/environment/data/packs/LEDGER.sha256`
- `tasks/battery-pack-thermal-conservation/environment/data/packs/pack_alpha.json`
- `tasks/battery-pack-thermal-conservation/environment/data/packs/pack_beta.json`
- `tasks/battery-pack-thermal-conservation/environment/data/packs/pack_gamma.json`
- `tasks/battery-pack-thermal-conservation/environment/data/refs/ship_ref.json`
- `tasks/battery-pack-thermal-conservation/environment/data/refs/fleet_ref.json`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: knit_x/op_a.py
  symbol: op_a
  kind: function
  signature: def op_a(a, b):
  purpose: resolve interface conductance from contact material id
- path: fold_y/op_b.py
  symbol: op_b
  kind: function
  signature: def op_b(a, b):
  purpose: accumulate canceling flux contributions into net cell update
- path: slot_z/op_c.py
  symbol: op_c
  kind: function
  signature: def op_c(a, b):
  purpose: select timestep policy token and advance one step
```

#### flipping_point_contract

```
locations:
  - id: A
    path: knit_x/op_a.py
    controls_tests: [test_k3_zircon, test_v4_jade]
  - id: B
    path: fold_y/op_b.py
    controls_tests: [test_p2_garnet, test_r1_onyx, test_w9_flint]
  - id: C
    path: slot_z/op_c.py
    controls_tests: [test_q7_topaz, test_t6_amber, test_m8_obsidian]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: bin/thermalsurf
  kind: helper
  rhymes_with: op_b
  non_fix_purpose: surface dashboard that prints ok without conservation checks
- path: docs/layout_notes.md
  kind: config-reader
  rhymes_with: op_a
  non_fix_purpose: describes pack folder layout without listing fix algebra
- path: solver/decoy/skim_w.py
  kind: module
  rhymes_with: op_c
  non_fix_purpose: logs probe temperatures for ops; not on conservation critical path
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [pack, thermal, energy, conservation, hotspot, contact, resistance, reduction, order, policy, profile, profiles, ship, fleet, solver, report, bands, fixture, fixtures, ledger, dashboard, residual, residuals, temperature, flux, rebuild, entrypoint, desk, cells, conductance]
```
