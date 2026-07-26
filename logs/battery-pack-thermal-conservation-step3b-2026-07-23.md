# Step 3b paper review — `battery-pack-thermal-conservation` (2026-07-23)

## Evidence (Step 2b)

| Gate | Result |
| --- | --- |
| `run_static_checks.py` / preflight | PASS |
| `collapse_check.py` | 0 FAIL / 4 WARN / 19 PASS (WARN overall) |
| Harbor oracle 1x | reward **1.0** (`jobs/2026-07-23__21-10-38`) |
| Harbor NOP | reward **0.0** (`jobs/2026-07-23__21-10-56`) |
| Docker cleanup | done after Step 2b |
| `.step2b-checksum` | present |

## Verdict (Step 3b only)

Paper review complete — **Ready for Step 4**. No task-file edits (no dirty-flag). Final ACCEPT / ACCEPT WITH NOTES / REJECT is Step 4 after oracle 10x + `approve_task.py`.

## Collapse WARN justifications

### RC1 — no comparable file deltas (WARN)

Oracle uses whole-module `cp` of `knit_x/op_a.py`, `fold_y/op_b.py`, `slot_z/op_c.py` from `solution/` over broken stubs. Checker cannot emit line-level deltas for replace-copy frontiers (same class as day-ahead). Net change is expansion, not deletion: env stubs are 7 / 10 / 6 LOC; oracle bodies are 29 / 29 / 21 LOC with material table, compensated reduction, and CFL/fixed dt policy. **Accept.**

### RC7 — 61 non-boilerplate LOC borderline (WARN)

A12 band 30–80. Three coupled physics loci (contact scale × canceling-flux fold × dt policy) across distinct package roots; each body is naturally short once the correct schedule is known. Expanding further would pad helper smoke checks already present in `derive.sh`, not harden the residual. Matches A16 WARN-band policy **(b)** — same class as day-ahead borderline LOC. **Accept.**

### RC8 — frontier concentration (WARN)

Checker folds targets under `${APP_ROOT:-/app}` and flags subsystem share on small files. **CR2 already PASSes:** 3 locations across 3 roots (`knit_x` / `fold_y` / `slot_z`); max single-location share 38% under the 50% cap. Concentration is a path-root / small-file artifact, not a one-function exploit. Flipping any one locus fails its declared residual/token cells while leaving others green. **Accept.**

### GX3 — edit distance 57 borderline (WARN)

Real added+removed non-comment content is 57 lines across the three targets (A12 borderline). Superseding comfort floor is 80; substantive delta already encodes the three independent schedules agents must rediscover. Cosmetic inflation forbidden by A16 anti-gaming. **Accept under A16 WARN-band policy (b).**

## 1. Structural review (`review-and-submit.mdc` §1–7)

| Section | Verdict | Note |
| --- | --- | --- |
| 1 Instruction | PASS | Symptoms-only; absolute paths; bands deferred to `/app/docs/thermal_bands.md`; no fix loci |
| 2 Environment | PASS | Pinned digest + apt; `.dockerignore`; thermalsurf via `tools/` → `/app/bin`; no solution/tests COPY |
| 3 Oracle | PASS | Deterministic cp + rebuild + double desk run; smoke asserts on repaired helpers |
| 4 Verifiers | PASS | Offline template `test.sh`; domain residual/token asserts; rebuild re-entry |
| 5 Metadata | PASS | `scientific-computing`, hard, small, `allow_internet=false`, anonymous author |
| 6 Structure | PASS | Standard layout; `output_contract.toml` present (zip-excluded) |
| 7 Difficulty | PASS | Collapse 0 FAIL; WARNs justified above; oracle 1.0 / NOP 0.0 |

## 2. LLM-level collapse audit (Part A)

- **Smallest plausible successful patch:** Restore material-dependent contact scale (`op_a`), compensated pairwise flux accumulation (`op_b`), and profile-token dt selection (`op_c`); rebuild; emit report via desk entrypoint.
- **Likely editable frontier:** `knit_x/op_a.py`, `fold_y/op_b.py`, `slot_z/op_c.py` (opaque); decoy `solver/decoy/skim_w.py` and `thermalsurf` are non-graded bait.
- **Requirement → file map:** energy/hotspot bands → all three loci + profiles; token fields → profile TOML echo through repaired ops; byte-identical runs → deterministic desk; rebuild re-entry → durable `/app` sources (not hand-written JSON).
- **Oracle LOC:** 61 non-boilerplate (borderline WARN); GX3 = 57 (borderline WARN).
- **Discoverability:** Instruction nouns do not name `op_*` / package roots (CR7 PASS). Profiles + bands doc give outcomes, not algebra.
- **Red flags:** None mechanical beyond the four justified WARNs. Residual risk: frontier agents pattern-match FV conservation stubs — mitigated by dual ship/fleet profiles and coupled residual×token cells.
- **Residual hardness:** Agents must rediscover three opaque physics schedules under dual profiles; fixing one leaves distant energy/hotspot/token cells red; surface `thermalsurf` greens while deep bands fail; verifier rebuild rejects hand-written reports.
- **Collapse verdict:** **PASS with notes** (RC1/RC7/RC8/GX3 WARN accept).

## 3. Per-test feasibility (Part B)

| Test | Grades | Single-approach | Chain | Order | Flaky | Niche | Risk |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `test_k3_zircon` | schema + ship/fleet ids | N | N | N | N | N | LOW |
| `test_v4_jade` | ship energy band | N | N | N | N | N | LOW |
| `test_p2_garnet` | hotspot + max_dT both profiles | N | N | N | N | N | MED |
| `test_r1_onyx` | tokens match profiles | N | N | N | N | N | LOW |
| `test_w9_flint` | byte-idempotent desk | N | N | N | N | N | LOW |
| `test_q7_topaz` | fleet energy band | N | N | N | N | N | LOW |
| `test_t6_amber` | thermalsurf ok ∧ deep bands | N | N | N | N | N | LOW |
| `test_m8_obsidian` | rebuild + report + ledger sha | N | N | N | N | N | LOW |

No HIGH-risk tests. No Step 3a-V escalation.

## Edit ledger

No task-file edits in Step 3b.

## Next action

Ready for Step 4 (oracle 10x + zip + `approve_task.py --skip-verifier-health` + fixture mirror + docker cleanup).
