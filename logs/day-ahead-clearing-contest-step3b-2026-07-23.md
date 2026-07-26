# Step 3b paper review — `day-ahead-clearing-contest` (2026-07-23)

## Evidence (Step 2b)

| Gate | Result |
| --- | --- |
| `run_static_checks.py` / preflight | PASS (`./scripts/check-task.sh`, after seal) |
| `collapse_check.py` | 0 FAIL / 6 WARN / 17 PASS (WARN overall) |
| Oracle 1x (pre-seal) | reward **1.0** (`jobs/2026-07-23__20-50-00`) |
| NOP (pre-seal) | reward **0.0** (`jobs/2026-07-23__20-50-33`) |
| Oracle 1x (post-seal) | reward **1.0** (`jobs/2026-07-23__20-55-55`) |
| NOP (post-seal) | reward **0.0** (`jobs/2026-07-23__20-56-21`) |
| Runtime jar membership | `core.pyc` + `__main__.py` only (no `core.py`) |
| `.step2b-checksum` | present (refreshed post-seal) |

## Verdict

**ACCEPT WITH NOTES** on the six collapse WARNs (games contest class; justified below).

## Redesign note (2026-07-23 evening)

Aligned to idea + `task-type-taxonomy.md` `games`:
- Sealed **Java** `fixtures/judge.jar` (languages `python`/`java`/`bash`); no repair/debug frontier
- Harder puzzle lattice + domain tests (status lattice, trap rejection, deep SMP via history notes, multi-unit non-naive clears)
- Oracle 10x **1.0**; NOP **0.0**; `approve_task.py` after Java cutover

## Collapse WARN justifications

### RC1 — no comparable file deltas (WARN)

Oracle copies *new* packages (`lane_knit` / `seat_fold` / `roll_emit`) into `/app`; there is no broken env baseline to diff. Expected for a contest booklet (agent synthesizes a card, not a polarity patch). Residual hardness is the 12-round status matrix under the judge, not env edit distance. **Accept.**

### RC7 — 51 non-boilerplate LOC borderline (WARN)

A12 band 30–80. **GX3 edit distance = 155 (PASS)** — superseding A16 metric. Substantive search lives in `op_b` enumeration + `op_c` emit; expanding further would pad, not harden. **Accept under A16 WARN-band policy (b).**

### RC8 — frontier concentration (WARN)

Checker folds all three targets under `${APP_ROOT:-/app}` (100% share) while still reporting three packages. CR2 already PASSes: 3 locations, max share 38%. Concentration is a path-root artifact of contest oracles that materialize under `/app`, not a single-file fix. **Accept.**

### CR1 — `op_a` / `op_b` / `op_c` missing from shipped env (WARN)

Symbols exist only under `solution/` and are copied at solve time. Manifest declares them for flipping-point bookkeeping; they are not agent-visible fix sites. Games pattern (oracle invents desk helpers). **Accept.**

### CR7 — no parseable oracle frontier (WARN)

Same root cause as CR1: no env files on the fix path to extract symbols from. Grep-resistance is vacuously N/A for a booklet task whose “frontier” is puzzle reasoning. Instruction nouns do not name `op_*`. **Accept.**

### GX7 — orphan path `/app/bin/judge.jar.sha256` (WARN)

Declared in `output_contract.toml` `internal_harness_files`; used by `test_m8_obsidian` anti-tamper. Instruction correctly omits internal harness paths. Path-literal WARN only (not FAIL). **Accept.**

## Part A residual hardness (post-WARN)

| Signal | Assessment |
| --- | --- |
| RC6 symptoms-only | PASS (0 families) |
| GX9 saturation | 26% — under threshold |
| Kiosk false-green | Present (`draft_*.txt` + sensei whisper) |
| Status lattice | 6 feasible / 3 reserve_short / 3 infeasible |
| Docs fairness | `contest_rules.md` states reserve_short vs infeasible + `C_RES`/`C_CAP` (weiqi sufficiency lesson) without pasting per-round answers |
| **Judge opacity** | **PASS at runtime** — zipapp has `core.pyc`, no `core.py` (build-time `judge_src/` still in zip for Docker COPY; not in image) |

## Part B — per-test feasibility

| Test | What it grades | Risk | Notes |
| --- | --- | --- | --- |
| `test_k3_zircon` | schema / nesting / status vocab | LOW | Schema also in `score_card.md` |
| `test_m8_obsidian` | judge checksum + desk idempotency | LOW | Re-entry; not chain-dependent |
| `test_p2_garnet` | feasible_clear + judge ok | MED | Multiple legal clears allowed |
| `test_q7_topaz` | reserve_short + `C_RES` | MED | Documented polarity |
| `test_r1_onyx` | infeasible + `C_CAP` | MED | Documented polarity |
| `test_t6_amber` | kiosk ≠ card on trap rounds | LOW | Divergence outcome |
| `test_v4_jade` | SMP = max cleared offer | MED | Matches rules prose |
| `test_w9_flint` | deep feasibles ≠ naive full dump | MED | Rejects full-cap dump |

No order sensitivity or wall-clock asserts. `verifier_health.py` not required for routine path.

## Instruction / category spot-check

- Category `games`, contest language, `/app/puzzles/`, `/app/bin/judge.jar`, `/app/kiosk/` — weiqi-shaped surface.
- Instruction symptoms-only; contract deferred to `/app/docs/`.
- `languages = ["python", "bash"]` matches stack (zipapp, not JVM).
- No `/tests` in instruction; absolute paths.

## Step 4 gate (when packaging)

1. Seal the zipapp (blocking for hardness).
2. Re-run `./scripts/check-task.sh tasks/day-ahead-clearing-contest` (checksum refresh).
3. Oracle 10x + confirm NOP still 0.0 if image changed.
4. Zip → `validate_submission_zip.py` → `approve_task.py --skip-verifier-health`.
5. `./scripts/cleanup-task-docker.sh day-ahead-clearing-contest`.
