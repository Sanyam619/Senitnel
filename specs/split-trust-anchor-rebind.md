### Decision
GO — Attempt 1. Symptoms-only public contract; distributed fix across vault/pinset/capdec roots; opaque symbol table; eight verifier slices with no instruction-noun leakage in test names.

### Metadata
- version: 2
- Task name: split-trust-anchor-rebind
- Title: Split Trust Anchor Rebind
- Category: security
- Languages: [C]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: []
- Tags: [mtls, trust-store, capability, c, admission, revocation]
- Milestones: 0

## Authoring Brief

### Public contract

The agent receives a compact C edge-gateway codebase that admits peers using three disagreeing authorities after a restore. Surface health still prints TLS OK while some peers that should be refused complete admission and some previously allowed peers fail only after capability material refresh.

The agent must drive the existing admission workflow so every bundled scenario under `/app/data/scenarios/` yields the correct decision and emit `/output/admit-ledger.json` with:

- `schema_version` (string, fixed value `edge-admit-1`)
- `cases` (array) — one object per scenario id with:
  - `id` (string)
  - `decision` (string: `accept` or `reject`)
  - `reason_code` (string)
- `reload_epoch` (non-negative integer matching `/app/data/state/runtime.json` field `epoch`)

After `/app/scripts/edge-reload.sh`, re-running admission must keep the same decisions for the same case ids. Do not alter `/app/bin/surfcheck` or remove scenario fixtures.

Grading checks per-case decisions and reason codes embedded in the verifier, reload stability, and ledger schema — not log text alone.

### Failure topology

Symptom cluster A: restore-era trust material still binds, so peers from the backup generation are admitted while runtime epoch has moved — indicates wrong generation bind, not a TLS stack failure. Symptom cluster B: pin material and subject lineage disagree but admission still allows — indicates pin scoring is skipped or always-match. Symptom cluster C: cached capability decode stays accept after fresh revocation bytes say otherwise — indicates cache-preferred decode on refresh windows.

These clusters interact: fixing only the trust store keeps TLS OK and may pass generation checks while revoked or wrong-lineage peers still succeed; fixing only freshness rejects stale cache cases but still admits restore-drift and pin-skew peers. The agent must coordinate all three authorities under conflict.

### Environment shape

- **`environment/src/vault/`** — on-disk trust material load and generation bind.
- **`environment/src/pinset/`** — runtime pin material load and lineage scoring.
- **`environment/src/capdec/`** — capability decode, cache view, and revocation freshness choice.
- **`environment/src/gate/`** — admission assembly from intermediate slots (distributed; no single file names all three fix symbols).
- **`environment/src/reload/`** — restore apply and runtime epoch read.
- **`environment/src/health/`** — surfcheck TLS OK path (bait; not the fix surface).
- **`environment/scripts/`** — run-admit and edge-reload entrypoints.
- **`environment/data/`** — restore snapshot, scenarios, pins, revocations, runtime state.
- **`environment/docs/`** — admit ledger schema note.

### Required artifacts

- `tasks/split-trust-anchor-rebind/instruction.md` — symptoms-only prose per Public contract.
- `tasks/split-trust-anchor-rebind/task.toml` — edition_2 standard task; `[environment] allow_internet = false`.
- `tasks/split-trust-anchor-rebind/environment/Dockerfile` — build toolchain + verifier deps.
- `tasks/split-trust-anchor-rebind/environment/.dockerignore`
- `tasks/split-trust-anchor-rebind/tests/test.sh` — canonical template.
- `tasks/split-trust-anchor-rebind/tests/test_outputs.py` — ≥8 tests per Test plan.
- `tasks/split-trust-anchor-rebind/solution/solve.sh` — oracle touching construction manifest symbols only.
- Full `environment/` tree per Initial Draft Commitments (30+ substantive files).

### Test plan

1. **test_emit_json_contract** — ledger exists, schema_version, required keys, reload_epoch matches runtime epoch.
2. **test_k9_slot_deny** — revoked capability case must reject with expected reason_code.
3. **test_m2_slot_allow** — fully aligned legitimate case must accept.
4. **test_n4_stale_window** — cached accept vs fresh revocation must reject.
5. **test_p7_skew_hot** — pin/lineage mismatch must reject despite healthy store path.
6. **test_q3_gen_skew** — restore-generation peer must reject under current runtime epoch.
7. **test_r8_hold_same** — decisions unchanged after edge-reload + re-admit.
8. **test_t1_rank_mix** — triple-authority conflict must reject with conflict reason_code.

Multiple valid internal orderings may pass if outcomes hold; tests check ledger outcomes not CLI flags.

### Drafting guardrails

Instruction stays symptoms-only: no precedence recipes, no module hints, no "debug/fix/bug" framing. Fix-path symbols use construction manifest opaque names only. Expected decisions live in test code (RC5). Decoy modules must compile and serve real non-fix paths. Do not name tests after instruction nouns. CR8: no single file references more than two symbol_table symbols.

### Triviality Ledger

- Naive trust-store-only edit passes surfcheck and may look healthy but fails `test_k9_slot_deny` / `test_n4_stale_window` because revocation freshness never wins.
- Pin-file-only edit passes `test_p7_skew_hot` locally but fails `test_q3_gen_skew` because restore generation still binds.
- Cache-clear-only edit passes stale-window but fails `test_t1_rank_mix` when lineage and generation still disagree.
- Hand-writing ledger JSON passes schema smoke but fails reload-hold when live admission path remains wrong.

### Per-gate Pitfall Inventory

- **RC1**: Oracle must implement real merge logic in three C files, not delete buggy branches only.
- **RC2**: No `broken_*`, `buggy_*`, `golden_*` in paths or test names.
- **RC3**: Every case decision and reason_code has a computed assertion, not existence-only.
- **RC4**: Expected decisions embedded in `test_outputs.py`, not agent-writable golden files.
- **RC5**: No answer-shaped ledger under `environment/`.
- **RC6**: Instruction describes symptoms and output schema only — no authority precedence recipe.
- **RC7**: Oracle touches ≥3 manifest locations with substantive LOC.
- **GX3**: Substantive C authority logic in oracle, not comment-padding.
- **CR8**: Gate assembly distributed so no file names all three merge symbols.
- **static checks**: `allow_internet = false`; pytest in Dockerfile; 20+ env files.

### Initial Draft Commitments

- `environment/Makefile`
- `environment/.dockerignore`
- `environment/Dockerfile`
- `environment/include/common.h`
- `environment/include/vault.h`
- `environment/include/pinset.h`
- `environment/include/capdec.h`
- `environment/include/gate.h`
- `environment/include/reload.h`
- `environment/include/health.h`
- `environment/src/main.c`
- `environment/src/vault/load_store.c`
- `environment/src/vault/op_a.c`
- `environment/src/vault/scan_roots.c`
- `environment/src/pinset/load_pins.c`
- `environment/src/pinset/op_b.c`
- `environment/src/pinset/probe_hot.c`
- `environment/src/capdec/decode_tok.c`
- `environment/src/capdec/op_c.c`
- `environment/src/capdec/cache_view.c`
- `environment/src/gate/slot_io.c`
- `environment/src/gate/assemble_x.c`
- `environment/src/gate/assemble_y.c`
- `environment/src/reload/apply_snap.c`
- `environment/src/reload/epoch_read.c`
- `environment/src/health/surf_tls.c`
- `environment/src/util/json_out.c`
- `environment/src/util/hexlib.c`
- `environment/scripts/run-admit.sh`
- `environment/scripts/edge-reload.sh`
- `environment/scripts/surfcheck`
- `environment/docs/admit-schema.md`
- `environment/docs/architecture.md`
- `environment/data/state/runtime.json`
- `environment/data/restore/trust.bundle`
- `environment/data/restore/pins.hot`
- `environment/data/restore/state.snap`
- `environment/data/trust/live.bundle`
- `environment/data/pins/active.set`
- `environment/data/revocations/current.rl`
- `environment/data/revocations/cached.rl`
- `environment/data/scenarios/k9.json`
- `environment/data/scenarios/m2.json`
- `environment/data/scenarios/n4.json`
- `environment/data/scenarios/p7.json`
- `environment/data/scenarios/q3.json`
- `environment/data/scenarios/t1.json`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: environment/src/vault/op_a.c
  symbol: merge_row_a
  kind: function
  signature: int merge_row_a(const struct row_a *x, struct slot_a *y)
  purpose: Binds on-disk trust material generation to the active runtime counter.

- path: environment/src/pinset/op_b.c
  symbol: merge_row_b
  kind: function
  signature: int merge_row_b(const struct row_b *x, struct slot_b *y)
  purpose: Scores runtime pin material against subject lineage bytes.

- path: environment/src/capdec/op_c.c
  symbol: merge_row_c
  kind: function
  signature: int merge_row_c(const struct row_c *x, struct slot_c *y)
  purpose: Chooses between cached decode and fresh revocation bytes.
```

#### flipping_point_contract

```
locations:
  - id: A
    path: environment/src/vault/op_a.c
    controls_tests: [test_emit_json_contract, test_q3_gen_skew, test_r8_hold_same]
  - id: B
    path: environment/src/pinset/op_b.c
    controls_tests: [test_p7_skew_hot, test_t1_rank_mix, test_m2_slot_allow]
  - id: C
    path: environment/src/capdec/op_c.c
    controls_tests: [test_k9_slot_deny, test_n4_stale_window]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: environment/src/vault/scan_roots.c
  kind: helper
  rhymes_with: merge_row_a
  non_fix_purpose: Read-only inventory of trust root labels for surfcheck diagnostics.

- path: environment/src/pinset/probe_hot.c
  kind: helper
  rhymes_with: merge_row_b
  non_fix_purpose: Hot-path pin probe used by health tooling, not admission scoring.

- path: environment/src/capdec/cache_view.c
  kind: helper
  rhymes_with: merge_row_c
  non_fix_purpose: Dumps cached decode views for operators; does not choose freshness.
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [edge, gateway, restore, peers, handshake, service, capability, blob, surfcheck, TLS, admission, outcomes, matrix, scenarios, ledger, schema_version, cases, reload_epoch, integer, epoch, decision, accept, reject, reason_code, files, sources, scripts, path, peer, admit, field, ids]
```
