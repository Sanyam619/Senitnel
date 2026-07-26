### Decision
GO — Attempt 1. Java signed-plugin multi-authority trust rebind (security, not debug/repair framing); distributed fix across tier_a/b/c; opaque resolve_a/b/c; nine hard scenario tests with jarcheck digest-only bait.

### Metadata
- version: 2
- Task name: signed-plugin-trust-rebind
- Title: Signed Plugin Trust Rebind
- Category: security
- Languages: ["Java"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: []
- Tags: ["signed-jar", "keystore", "plugin", "java", "trust", "admission"]
- Milestones: 0

## Authoring Brief

### Public contract

A Java host loads signed plugins from a local catalog after a recent key-rotation and trust-store refresh. Observed load behavior disagrees with authorization intent: some plugins still enter with stale grants, some correctly signed plugins are refused when the wrong keystore lineage is consulted, and a local verifier tool often blesses a configuration that the host later rejects (or the reverse).

Drive the host admission path so every bundled scenario under `/app/data/scenarios/` yields the correct accept or reject decision. Emit `/output/plugin-ledger.json` containing:

- `schema_version` (string, fixed value `plugin-admit-1`)
- `cases` (array) — one object per scenario id with:
  - `id` (string)
  - `decision` (string: `accept` or `reject`)
  - `reason_code` (string)
- `reload_epoch` (non-negative integer matching `/app/data/state/runtime.json` field `epoch`)

After `/app/scripts/host-reload.sh`, repeating admission must preserve the same decisions for the same case ids. Do not modify `/app/bin/jarcheck` and do not remove scenario fixtures.

Grading checks per-case decisions and reason codes embedded in the verifier, reload stability, and ledger schema — not log text alone. This is an authority-rebind security outcome task; instruction must not use debug/repair framing.

### Failure topology

Symptom cluster A: post-rotation keystore material still binds an obsolete generation, so plugins from the prior root enter or valid current-root signers are refused — wrong lineage selection, not a missing JAR. Symptom cluster B: grant rows remain from the pre-refresh tape and still authorize under signer identity that no longer matches active lineage — grant-scope drift. Symptom cluster C: module-layer wiring completes from a pre-refresh snapshot while `jarcheck` only digests JAR bytes and blesses layouts the host will later refuse (or the reverse).

These clusters interact: fixing only lineage may pass signature-looking checks while stale grants still enter; fixing only grants rejects stale rows but still mis-wires layers and disagrees with jarcheck; fixing only layer install leaves wrong-lineage accepts. The agent must coordinate all three authorities under conflict.

### Environment shape

- **`environment/src/tier_a/`** — generation-bound root selection (`resolve_a`) plus digest-only decoy.
- **`environment/src/tier_b/`** — grant-scope binding to signer identity (`resolve_b`) plus tape-list decoy.
- **`environment/src/tier_c/`** — module-layer install and ledger emit (`resolve_c`).
- **`environment/src/host/`** — admission driver assembling the three slots (distributed; no single file names all three fix symbols).
- **`environment/bin/`** — `jarcheck` digest-only surface bait (must not be altered by agent).
- **`environment/scripts/`** — run-admit and host-reload entrypoints.
- **`environment/data/`** — keystores by generation, grants, layers, scenarios, runtime state.
- **`environment/docs/`** — ledger schema note only.

### Required artifacts

- `tasks/signed-plugin-trust-rebind/instruction.md` — symptoms-only prose per Public contract; no debug/repair language.
- `tasks/signed-plugin-trust-rebind/task.toml` — edition_2 standard task; `category = "security"`; `[environment] allow_internet = false`.
- `tasks/signed-plugin-trust-rebind/environment/Dockerfile` — JDK toolchain + verifier deps.
- `tasks/signed-plugin-trust-rebind/environment/.dockerignore`
- `tasks/signed-plugin-trust-rebind/tests/test.sh` — canonical template.
- `tasks/signed-plugin-trust-rebind/tests/test_outputs.py` — ≥9 hard tests per Test plan (no existence-only smoke).
- `tasks/signed-plugin-trust-rebind/solution/solve.sh` — oracle touching construction manifest symbols only.
- Full `environment/` tree per Initial Draft Commitments (30+ substantive files).

### Test plan

1. **test_v6_flint** — ledger exists; schema_version, required keys, reload_epoch matches runtime epoch.
2. **test_k9_zircon** — wrong-lineage scenario must reject with expected reason_code.
3. **test_m2_feldspar** — fully aligned legitimate scenario must accept.
4. **test_n4_garnet** — stale grant after refresh must reject despite verifying signature bytes.
5. **test_p7_topaz** — revoke-then-refresh ordering under active lineage must refuse revoked signer.
6. **test_q3_onyx** — missing/wrong module-layer wire must reject.
7. **test_r8_amber** — jarcheck digestive blessing must not dictate host decision when authorities conflict.
8. **test_w2_quartz** — decisions unchanged after host-reload + re-admit.
9. **test_t1_shale** — triple-authority conflict must reject with conflict reason_code.

Multiple valid internal orderings may pass if outcomes hold; tests check ledger outcomes not CLI flags. No trivial presence-only tests.

### Drafting guardrails

Instruction stays symptoms-only: no precedence recipes, no module hints, no debug/repair/bug framing. Fix-path symbols use construction manifest opaque names only. Expected decisions live in test code (RC5). Decoy modules must compile and serve real non-fix paths. Do not name tests after instruction nouns. CR8: no single file references more than two symbol_table symbols.

### Triviality Ledger

- Naive keystore-file swap may calm jarcheck-adjacent intuition but fails `test_n4_garnet` / `test_t1_shale` because grant scope and layer wiring stay wrong.
- Grant-tape-only edit passes stale-grant locally but fails `test_k9_zircon` because obsolete lineage still binds.
- Layer-manifest-only edit passes `test_q3_onyx` locally but fails `test_r8_amber` / `test_w2_quartz` when host still disagrees under reload.
- Trusting jarcheck digest-only output as oracle truth fails `test_r8_amber` by design.
- Hand-writing ledger JSON passes schema smoke but fails reload-hold when live admission path remains wrong.

### Per-gate Pitfall Inventory

- **RC1**: Oracle must implement real resolve logic in three Java files, not delete buggy branches only.
- **RC2**: No `broken_*`, `buggy_*`, `golden_*` in paths or test names.
- **RC3**: Every case decision and reason_code has a computed assertion, not existence-only.
- **RC4**: Expected decisions embedded in `test_outputs.py`, not agent-writable golden files.
- **RC5**: No answer-shaped ledger under `environment/`.
- **RC6**: Instruction describes symptoms and output schema only — no authority precedence recipe; no debug/repair wording.
- **RC7**: Oracle touches ≥3 manifest locations with substantive LOC.
- **GX3**: Substantive Java authority logic in oracle, not comment-padding.
- **CR8**: Host assembly distributed so no file names all three resolve symbols.
- **static checks**: `allow_internet = false`; pytest in Dockerfile; 20+ env files; category `security`.

### Initial Draft Commitments

- `tasks/signed-plugin-trust-rebind/task.toml`
- `tasks/signed-plugin-trust-rebind/instruction.md`
- `tasks/signed-plugin-trust-rebind/tests/test.sh`
- `tasks/signed-plugin-trust-rebind/tests/test_outputs.py`
- `tasks/signed-plugin-trust-rebind/solution/solve.sh`
- `tasks/signed-plugin-trust-rebind/environment/Dockerfile`
- `tasks/signed-plugin-trust-rebind/environment/.dockerignore`
- `tasks/signed-plugin-trust-rebind/environment/Makefile`
- `tasks/signed-plugin-trust-rebind/environment/src/tier_a/OpAlpha.java`
- `tasks/signed-plugin-trust-rebind/environment/src/tier_a/ScanDigest.java`
- `tasks/signed-plugin-trust-rebind/environment/src/tier_b/OpBeta.java`
- `tasks/signed-plugin-trust-rebind/environment/src/tier_b/TapeRead.java`
- `tasks/signed-plugin-trust-rebind/environment/src/tier_c/OpGamma.java`
- `tasks/signed-plugin-trust-rebind/environment/src/host/AdmitDriver.java`
- `tasks/signed-plugin-trust-rebind/environment/src/host/SlotIO.java`
- `tasks/signed-plugin-trust-rebind/environment/src/host/AssembleX.java`
- `tasks/signed-plugin-trust-rebind/environment/src/host/AssembleY.java`
- `tasks/signed-plugin-trust-rebind/environment/src/util/JsonOut.java`
- `tasks/signed-plugin-trust-rebind/environment/src/util/HexLib.java`
- `tasks/signed-plugin-trust-rebind/environment/src/util/EpochRead.java`
- `tasks/signed-plugin-trust-rebind/environment/bin/jarcheck`
- `tasks/signed-plugin-trust-rebind/environment/scripts/run-admit.sh`
- `tasks/signed-plugin-trust-rebind/environment/scripts/host-reload.sh`
- `tasks/signed-plugin-trust-rebind/environment/docs/admit-schema.md`
- `tasks/signed-plugin-trust-rebind/environment/docs/architecture.md`
- `tasks/signed-plugin-trust-rebind/environment/data/state/runtime.json`
- `tasks/signed-plugin-trust-rebind/environment/data/roots/gen0.bundle`
- `tasks/signed-plugin-trust-rebind/environment/data/roots/gen1.bundle`
- `tasks/signed-plugin-trust-rebind/environment/data/grants/active.tape`
- `tasks/signed-plugin-trust-rebind/environment/data/grants/stale.tape`
- `tasks/signed-plugin-trust-rebind/environment/data/layers/wire.snap`
- `tasks/signed-plugin-trust-rebind/environment/data/layers/pre.snap`
- `tasks/signed-plugin-trust-rebind/environment/data/revocations/current.rl`
- `tasks/signed-plugin-trust-rebind/environment/data/scenarios/k9.json`
- `tasks/signed-plugin-trust-rebind/environment/data/scenarios/m2.json`
- `tasks/signed-plugin-trust-rebind/environment/data/scenarios/n4.json`
- `tasks/signed-plugin-trust-rebind/environment/data/scenarios/p7.json`
- `tasks/signed-plugin-trust-rebind/environment/data/scenarios/q3.json`
- `tasks/signed-plugin-trust-rebind/environment/data/scenarios/r8.json`
- `tasks/signed-plugin-trust-rebind/environment/data/scenarios/t1.json`
- `tasks/signed-plugin-trust-rebind/environment/data/scenarios/w2.json`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: environment/src/tier_a/OpAlpha.java
  symbol: resolve_a
  kind: function
  signature: boolean resolve_a(String a, String b)
  purpose: Selects generation-bound root bytes and returns whether the candidate matches active epoch material.

- path: environment/src/tier_b/OpBeta.java
  symbol: resolve_b
  kind: function
  signature: boolean resolve_b(String a, String b, String c)
  purpose: Binds permission rows to signer identity under the selected root and refuses stale rows.

- path: environment/src/tier_c/OpGamma.java
  symbol: resolve_c
  kind: function
  signature: boolean resolve_c(String a, String b)
  purpose: Completes module-layer install after refresh and writes the admission ledger rows.
```

#### flipping_point_contract

```
locations:
  - id: A
    path: environment/src/tier_a/OpAlpha.java
    controls_tests: [test_k9_zircon, test_m2_feldspar, test_t1_shale]
  - id: B
    path: environment/src/tier_b/OpBeta.java
    controls_tests: [test_n4_garnet, test_p7_topaz, test_t1_shale]
  - id: C
    path: environment/src/tier_c/OpGamma.java
    controls_tests: [test_q3_onyx, test_r8_amber, test_v6_flint, test_w2_quartz]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: environment/src/tier_a/ScanDigest.java
  kind: helper
  rhymes_with: resolve_a
  non_fix_purpose: Hashes JAR bytes for jarcheck surface checks; never consults generation-bound roots.

- path: environment/src/tier_b/TapeRead.java
  kind: helper
  rhymes_with: resolve_b
  non_fix_purpose: Lists permission tape rows for diagnostics without binding identity or refusing stale rows.
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [java, host, plugins, catalog, key-rotation, trust-store, refresh, load, behavior, authorization, intent, grants, enter, signed, refused, keystore, lineage, verifier, tool, configuration, reject, reverse, admission, path, scenario, scenarios, accept, decision, emit, output, plugin-ledger, schema_version, plugin-admit-1, cases, array, objects, id, reason_code, reload_epoch, epoch, field, state, runtime, scripts, host-reload, repeating, preserve, modify, jarcheck, fixtures, case, ids, local]
```
