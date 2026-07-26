### Decision
GO — Attempt 1. Symptoms-only public contract; distributed fix across forge/ledger/mesh roots; opaque symbol table; eight verifier slices with no instruction-noun leakage in test names.

### Metadata
- Task name: amr-ghost-cell-rebind-restart
- Title: AMR Ghost-Cell Rebind Restart
- Category: scientific-computing
- Languages: [C]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: [amr, checkpoint, hydrodynamics, c, restart, numerical]
- Milestones: 0

### Discovery budget

- Discovery: Which archived generation id is canonical after the layout-directive merge (cycle 21 blob vs cycle 17 blob).
  Planned location: `environment/src/ledger/epoch_pick.c` plus merge metadata in `environment/data/policy_v2.table`
  Why instruction must not reveal it: Naming the generation would collapse search to a single blob pick.

- Discovery: Recovery stages must run layout reconciliation before neighbor link refresh before field attach (stage mask ordering in `apply_seq_a`).
  Planned location: `environment/src/forge/recover_phase.c` stage bitmask and driver in `environment/scripts/run_restart.sh`
  Why instruction must not reveal it: Stating order turns the task into recipe transcription.

- Discovery: Cross-level halo orientation uses a signed axis convention encoded in link refresh, not in hydro flux kernels.
  Planned location: `environment/src/mesh/link_refresh.c` and `environment/src/couple/halo_fill.c` interaction
  Why instruction must not reveal it: Naming orientation convention lets agents patch one constant without understanding topology coupling.

### Anti-trivialization verdict

| # | Check | Verdict | Reasoning |
|---|-------|---------|-----------|
| 1 | Disclosure-collapse | PASS | Instruction states symptoms and output schema only; fix path requires codebase discovery. |
| 2 | Hidden-instance | PASS | All scenarios share one broken recovery path; not a find-the-one-file puzzle. |
| 3 | Single-artifact repair | PASS | No single manifest/checksum flip passes slice + mass + depth tests together. |
| 4 | Generalization | PASS | Three fixtures with distinct refinement ladders exercise the same invariant class. |
| 5 | Prompt-honesty | PASS | Honest symptoms-only prompt does not reveal generation id or stage order. |
| 6 | Cheating-vs-difficulty | PASS | Anti-tamper measures (computed L2 in tests) support verification, not artificial hardness. |
| 7 | Mechanical-fix filter | PASS | Core difficulty is domain coordination, not verifier formatting. |
| 8 | Localized-fix | PASS | Flipping-point contract spans forge, ledger, mesh roots. |
| 9 | Oracle-locality | PASS | Oracle coordinates three modules; no single-file wholesale replace. |
| 10 | Small declarative-cluster | PASS | Fix is procedural coordination across drivers, not one table edit. |
| 11 | Grep-collapse | PASS | Instruction nouns banned from fix-path symbols; opaque names in code. |
| 12 | Pre-factored-helper | PASS | Decoys (`catalog_scan`, `stencil_probe`) do real work; fix symbols are opaque. |
| 13 | Recipe-discount | PASS | Standard checkpoint-resume recipe fails without generation + ordering discoveries. |
| 14 | Security-aura discount | PASS | Hardness is numerical/topological coupling, not security vocabulary. |
| 15 | Orthogonal-checklist | PASS | Generation choice, stage order, and link refresh are coupled — fixing one in isolation fails chain test. |
| 16 | Harness-discount | PASS | Docker/C build realism does not substitute for reasoning. |
| 17 | One-pass solvability | PASS | Agent must read driver, catalog, and mesh code across roots before acting. |
| 18 | Hard-only gate | PASS | Clearly hard on all five axes; not medium. |
| 19 | Discovery budget test | PASS | Three non-trivial discoveries enumerated above. |
| 20 | Instruction specificity test | PASS | Symptoms-only — no cause naming. |
| 21 | Topology distribution test | PASS | Three distinct fix topologies below, each ≥3 locations. |

### Topology enumeration (3 candidate fix topologies)

**Topology A — Wrong recovery stage order**
- Locations: `environment/src/forge/recover_phase.c` (`apply_seq_a`), `environment/scripts/run_restart.sh`, `environment/src/mesh/link_refresh.c` (`rebuild_map_c`)
- Why no single location suffices: Correct stage mask in forge without link refresh still yields stale halos; link refresh alone before layout reconcile breaks depth ladder.

**Topology B — Wrong archived generation binding**
- Locations: `environment/src/ledger/epoch_pick.c` (`select_src_b`), `environment/src/ledger/policy_merge.c`, `environment/src/forge/checkpoint_io.c`
- Why no single location suffices: Picking the wrong blob corrupts tree shape; IO layer alone cannot fix merge metadata interpretation; merge module alone cannot refresh links.

**Topology C — Partial neighbor table refresh**
- Locations: `environment/src/mesh/link_refresh.c` (`rebuild_map_c`), `environment/src/couple/halo_fill.c`, `environment/src/mesh/block_tree.c`
- Why no single location suffices: Intra-level refresh without block tree reconcile passes local alpha but fails gamma cross-level invariant; halo fill alone cannot infer correct links.

### Rubric axes

| Axis | Verdict | Reasoning |
|------|---------|-----------|
| Verifiable | PASS | Deterministic L2, mass, depth, and schema checks on fixed fixtures. |
| Well-specified | PASS | Public contract + summary schema doc define equivalent verifier interpretations. |
| Solvable | PASS | Expert with AMR restart experience can complete in a few hours on this codebase size. |
| Difficult | PASS | Requires multi-phase recovery reasoning beyond generic checkpoint resume. |
| Interesting | PASS | Real HPC ops pain — policy migration on archived AMR state. |
| Outcome-verified | PASS | Grades field norms and summary JSON, not CLI steps. |

### Hardness axes

| Axis | Verdict | Reasoning |
|------|---------|-----------|
| Discover | PASS | Generation id, stage order, and halo convention must be inferred from code and archives. |
| Synthesize | PASS | Ledger, forge driver, mesh links, and couple halos must form one mental model. |
| Diagnose | PASS | Instruction reports face-layer drift and plausible interiors — not root cause. |
| Navigate coupling | PASS | Local reorder breaks mass on one scenario while passing another. |
| Reason beyond training | PASS | AMR hierarchical recovery coupling is specialized domain reasoning. |

### Instruction completeness test

**Verdict: PASS (agent cannot solve from instruction alone).**

The instruction names observable drift and required outputs but not which archived generation binds, which recovery stages exist, or their order. Without reading `run_restart.sh`, `recover_phase.c`, and `epoch_pick.c`, an agent cannot produce passing face L2 or chain-dependent gamma results.

## Reviewer Appendix

### Implementation plan

Ship a ~35-file C mini-AMR hydro code with working flux kernels and a broken default recovery path: the restart script calls stages in the wrong order and binds the pre-merge archived generation. The oracle selects generation 21, sets stage mask to layout-then-links-then-attach, and reruns restart for all fixtures. Verifier embeds expected L2/mass from reference slices and fixture params. Difficulty survives because multiple modules look authoritative (catalog scan, default script, policy table) and premature success on alpha masks gamma failure.

### Proposed file inventory

See Initial Draft Commitments in authoring spec — 35 substantive environment files across hydro, mesh, forge, ledger, couple, scripts, docs, and data domains.

### Oracle notes

`solve.sh` builds the project, patches or invokes `select_src_b` path to return generation 21, sets `apply_seq_a` stage mask `0b111` in correct order via `run_restart.sh` env or sed on stage constants, runs restart for alpha/beta/gamma, verifies `/output/restart-summary.json` and field dumps exist. No physics rewrite — only recovery orchestration.

### Collapse audit

Stage: implementation-plan

Smallest plausible successful patch:
Coordinate generation selection in ledger, stage ordering in forge driver, and link refresh in mesh — roughly 40–80 lines across three files plus script invocation tweak; no single-location patch passes all eight tests.

Likely editable frontier:
- `environment/src/ledger/epoch_pick.c`
- `environment/src/forge/recover_phase.c`
- `environment/src/mesh/link_refresh.c`
- `environment/scripts/run_restart.sh`

Requirement-to-file map:
- Face L2 match → link refresh + correct generation
- Mass drift → halo fill after correct links
- Tree depth → generation + layout reconcile
- Summary schema → json emit after successful restart

Oracle estimated complexity: ~60 lines substantive shell + C invocation logic

Red flags:
- Generic checkpoint-resume cliché mitigated by distributed topology coupling and chain-dependent gamma test

Residual hardness:
Agent must trace multi-phase driver, reject decoy catalog tooling, and discover signed halo convention through code reading — not grep for "ghost" or "rebind."

Collapse verdict: PASS

### Naming-pass record

**Instruction nouns extracted:**
hydrodynamics, adaptive, refinement, checkpoints, hierarchical, blocks, cycle, archived, checkpoint, layout, restart, conserved, face, layer, norms, reference, baseline, interior, states, solver, kernels, recovery, scenarios, output, summary, block, counts, boundary, error, driver, snapshot, directive, magnitudes, traces, cells, fields, timesteps, policy, merge, topology, ghost, rebind, exchange, halo, neighbor, epoch, fixture

**Renames during drafting:**
- `pick_epoch` → `select_src_b`: overlaps forbidden noun epoch
- `rebind_topology` → `rebuild_map_c`: overlaps forbidden nouns rebind/topology
- `run_recovery_stages` → `apply_seq_a`: overlaps forbidden noun recovery

**Test names audited:**
- test_emit_json_contract
- test_slice_l2_alpha
- test_slice_l2_beta
- test_volume_sum_alpha
- test_volume_sum_beta
- test_depth_alpha
- test_depth_beta
- test_secondary_gamma

**Concentration math:**
- Total tests across `flipping_point_contract`: 8
- Per location:
  - A (`environment/src/forge/recover_phase.c`): 3/8 = 0.375
  - B (`environment/src/ledger/epoch_pick.c`): 3/8 = 0.375
  - C (`environment/src/mesh/link_refresh.c`): 2/8 = 0.25
- Cap: 0.5. Max ratio observed: 0.375. Status: PASS

### Per-test feasibility pre-check

- Test: test_emit_json_contract
- Checks: Summary JSON schema and required keys.
- Valid approaches: 1
- Chain-dependent: no
- Feasibility risk: LOW

- Test: test_slice_l2_alpha
- Checks: Face-layer L2 for alpha scenario.
- Valid approaches: 2+ (multiple valid stage orderings if invariants hold)
- Chain-dependent: yes — needs correct generation + links
- Feasibility risk: LOW

- Test: test_slice_l2_beta
- Checks: Face-layer L2 for beta scenario.
- Valid approaches: 2+
- Chain-dependent: yes
- Feasibility risk: LOW

- Test: test_volume_sum_alpha
- Checks: Global mass drift epsilon for alpha.
- Valid approaches: 2+
- Chain-dependent: yes — halo fill after links
- Feasibility risk: LOW

- Test: test_volume_sum_beta
- Checks: Mass drift for beta.
- Valid approaches: 2+
- Chain-dependent: yes
- Feasibility risk: LOW

- Test: test_depth_alpha
- Checks: Tree depth and block tally vs policy for alpha.
- Valid approaches: 1–2
- Chain-dependent: yes — generation binding
- Feasibility risk: LOW

- Test: test_depth_beta
- Checks: Depth/tally for beta.
- Valid approaches: 1–2
- Chain-dependent: yes
- Feasibility risk: LOW

- Test: test_secondary_gamma
- Checks: Third scenario chain — fails on wrong stage order even if alpha passes.
- Valid approaches: 1 (must satisfy full pipeline)
- Chain-dependent: yes — cross-level ladder
- Feasibility risk: MEDIUM
