### Decision
GO — Attempt 1. Security cutover (no repair/debug framing), distributed across wire/hold/stamp Java loci, opaque op_a/op_b/op_c, false-green findscan, soft-token multi-slot session semantics.

### Metadata
- version: 2
- Task name: pkcs11-multi-slot-session-rebind
- Title: PKCS#11 Multi-Slot Session Rebind
- Category: security
- Languages: ["Java"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: ["tool_specific"]
- Tags: ["pkcs11", "java", "hsm", "sessions", "slots", "crypto"]
- Milestones: 0

## Authoring Brief

### Public contract

A Java host under `/opt/pk11/` drives a software PKCS#11 module with multiple slots under `/data/token/`. After key rotation and restore drills, signing and verify calls still complete while an offline object scan stays green, yet live crypto work binds the wrong slot and PIN-cached sessions outlive the posted policy. `/opt/pk11/bin/findscan` reports matching object counts; `/opt/pk11/scripts/auth-stub.sh` exits non-zero. Leave `/data/fixtures/token-seed/` untouched.

**Required outcomes:**
- `/output/session-rebind.json` exists with integer `version` `1`.
- Array `slots`: each row has integer `id`, string `role` (`live` or `archive`), boolean `provider_bound`. Exactly one live slot with `provider_bound` reflecting the current lane; archive slots not provider-bound.
- Array `sessions`: each row has integer `slot_id`, boolean `pin_alive`, integer `ttl_sec`. Current-lane sessions must be `pin_alive` with `ttl_sec` honoring posted policy after reload.
- Array `certs`: each row has string `label`, integer `slot_id`, boolean `handle_auth`. Cert identity for required labels must sit on the current lane with `handle_auth`; stale prior-lane rows must not authorize.
- Runtime authorizer (`/opt/pk11/bin/authcheck`) accepts crypto only on the post-restore live slot under those invariants.

**Constraints:**
- `[environment] allow_internet = false`; verifier deps in Dockerfile.
- No multi-container layout.
- Cutover framing — agent completes incomplete Java rebind surfaces; instruction must not use repair/debug language.
- Language surface is Java (plus bash wrappers for CLIs).

### Failure topology

Three interacting clusters. First, false-green surface: `findscan` counts objects across slots and ignores provider bind and session lineage. Second, after restore, duplicate labels exist on archive and live slots while the provider still binds the archive id. Third, PIN login markers outlive posted `ttl_sec` across simulated reload, and cert handles remain on archive until label re-anchor — offline presence stays green while runtime authorization rejects.

Hard because no single keystore edit reconciles slot selection, session/PIN freshness, and cert handle vs label identity under adversarial reload fixtures.

### Environment shape

- `environment/Dockerfile` + `.dockerignore` — JDK 21, python3/pytest, token lab under `/data/token/`.
- `environment/wire/` — `OpA` fix-path + `LabelPick` decoy.
- `environment/hold/` — `OpB` fix-path + `CacheKeep` decoy.
- `environment/stamp/` — `OpC` fix-path.
- `environment/lib/` — shared token IO, handle map, JSON emit helpers.
- `environment/cmd/` — opaque CLIs: findscan, slotprobe, wireapply, holdrun, emitout, authcheck.
- `environment/config/` — posted PIN policy and path notes only.
- `environment/scripts/` — auth-stub and reload harness.
- `environment/data/` — fixture builder + token-seed anchor + multi-slot token state.

### Required artifacts

- `tasks/pkcs11-multi-slot-session-rebind/task.toml` with `allow_internet = false`, `category = "security"`, `languages = ["Java"]`.
- `instruction.md` — symptoms-only cutover; names output path and JSON fields; no repair/debug framing.
- `tests/test.sh`, `tests/test_outputs.py` — six opaque hard tests.
- `solution/solve.sh` — oracle completes three Java loci (≥30 LOC substantive).
- `environment/**` — 25+ non-Docker files per Initial Draft Commitments.

### Test plan

- `test_w4_cobal` — exactly one live slot with `provider_bound` true; archive not bound.
- `test_n7_quartz` — authcheck accepts signing/verify only when provider is on live slot id from fixtures.
- `test_h2_jade` — live-slot sessions have `pin_fresh` true after reload harness.
- `test_v9_felsic` — `ttl_sec` on live sessions does not exceed posted policy window after reload.
- `test_s5_basalt` — required cert labels have `handle_valid` true on live `slot_id`; archive stale handles fail.
- `test_m1_rhyolite` — ledger schema: version 1 with required `slots`/`sessions`/`certs` fields.

Multiple valid cutover edits allowed if outcomes match. Chain-dependent: auth/cert tests need bind + session freshness first.

### Drafting guardrails

Do not embed instruction nouns in fix-path symbols, parameters, or test names. Instruction may use standard PKCS#11 language. No repair/debug TODOs. findscan must genuinely implement shallow object-count checks. No HINT walkthroughs under environment/.

### Triviality Ledger

- Calling LabelPick (first matching label) keeps findscan green but fails live-slot provider_bound and authcheck tests.
- Completing op_a alone leaves pin_fresh false / ttl over policy → test_h2_jade / test_v9_felsic fail.
- Completing op_b alone without live bind fails test_w4_cobal / test_n7_quartz.
- Re-anchoring certs without op_a/op_b leaves archive authorization paths and fails freshness/identity coupling.
- CacheKeep decoy extends PIN forever for offline tools but never refreshes runtime session lineage.
- Touching token-seed fails fixture integrity checks embedded beside schema/auth tests.

### Per-gate Pitfall Inventory

- RC1: Oracle adds substantive Java cutover logic — never delete-bug or wholesale restore golden.
- RC3: Tests assert provider_bound, pin_fresh, ttl policy, handle_valid, authcheck — not mere file existence.
- RC5: Expected live slot ids / labels / ttl live in test code and fixtures, not golden under environment answer files.
- RC6: Instruction symptoms-only — no op_a / bind order / handle-vs-label recipe.
- RC7: solve.sh Java edits ≥30 substantive LOC.
- CR1/CR2: Construction manifest symbols verbatim; 2+2+2 flip split.
- CR7/GX9: JSON field names in instruction; numeric slot ids only from fixtures/runtime.
- Static: allow_internet=false, .dockerignore, absolute paths, category security, languages Java.

### Initial Draft Commitments

- `tasks/pkcs11-multi-slot-session-rebind/task.toml`
- `tasks/pkcs11-multi-slot-session-rebind/instruction.md`
- `tasks/pkcs11-multi-slot-session-rebind/output_contract.toml`
- `tasks/pkcs11-multi-slot-session-rebind/tests/test.sh`
- `tasks/pkcs11-multi-slot-session-rebind/tests/test_outputs.py`
- `tasks/pkcs11-multi-slot-session-rebind/solution/solve.sh`
- `tasks/pkcs11-multi-slot-session-rebind/environment/Dockerfile`
- `tasks/pkcs11-multi-slot-session-rebind/environment/.dockerignore`
- `tasks/pkcs11-multi-slot-session-rebind/environment/Makefile`
- `tasks/pkcs11-multi-slot-session-rebind/environment/wire/OpA.java`
- `tasks/pkcs11-multi-slot-session-rebind/environment/wire/LabelPick.java`
- `tasks/pkcs11-multi-slot-session-rebind/environment/hold/OpB.java`
- `tasks/pkcs11-multi-slot-session-rebind/environment/hold/CacheKeep.java`
- `tasks/pkcs11-multi-slot-session-rebind/environment/stamp/OpC.java`
- `tasks/pkcs11-multi-slot-session-rebind/environment/lib/TokenIo.java`
- `tasks/pkcs11-multi-slot-session-rebind/environment/lib/HandleMap.java`
- `tasks/pkcs11-multi-slot-session-rebind/environment/lib/JsonOut.java`
- `tasks/pkcs11-multi-slot-session-rebind/environment/lib/Paths.java`
- `tasks/pkcs11-multi-slot-session-rebind/environment/cmd/findscan/Main.java`
- `tasks/pkcs11-multi-slot-session-rebind/environment/cmd/slotprobe/Main.java`
- `tasks/pkcs11-multi-slot-session-rebind/environment/cmd/wireapply/Main.java`
- `tasks/pkcs11-multi-slot-session-rebind/environment/cmd/holdrun/Main.java`
- `tasks/pkcs11-multi-slot-session-rebind/environment/cmd/authcheck/Main.java`
- `tasks/pkcs11-multi-slot-session-rebind/environment/cmd/emitout/Main.java`
- `tasks/pkcs11-multi-slot-session-rebind/environment/config/lab.toml`
- `tasks/pkcs11-multi-slot-session-rebind/environment/config/pin_policy.toml`
- `tasks/pkcs11-multi-slot-session-rebind/environment/scripts/auth-stub.sh`
- `tasks/pkcs11-multi-slot-session-rebind/environment/scripts/reload-harness.sh`
- `tasks/pkcs11-multi-slot-session-rebind/environment/scripts/build-clis.sh`
- `tasks/pkcs11-multi-slot-session-rebind/environment/data/build_fixtures.sh`
- `tasks/pkcs11-multi-slot-session-rebind/environment/data/fixtures/token-seed/.keep`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: environment/wire/OpA.java
  symbol: op_a
  kind: function
  signature: static int op_a(Path a, Path b)
  purpose: Writes provider bind state selecting the post-restore live slot id from token inventory.

- path: environment/hold/OpB.java
  symbol: op_b
  kind: function
  signature: static int op_b(Path a, Path b, int c)
  purpose: Refreshes session lineage and PIN freshness against posted ttl across reload markers.

- path: environment/stamp/OpC.java
  symbol: op_c
  kind: function
  signature: static int op_c(Path a, Path b, Path c)
  purpose: Re-anchors cert identity to live slot by label, invalidates stale handles, emits session-rebind.json.
```

#### flipping_point_contract

```
locations:
  - id: A
    path: environment/wire/OpA.java
    controls_tests: [test_w4_cobal, test_n7_quartz]
  - id: B
    path: environment/hold/OpB.java
    controls_tests: [test_h2_jade, test_v9_felsic]
  - id: C
    path: environment/stamp/OpC.java
    controls_tests: [test_s5_basalt, test_m1_rhyolite]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: environment/wire/LabelPick.java
  kind: helper
  rhymes_with: op_a
  non_fix_purpose: Picks first slot that has a matching object label count; used by findscan diagnostics; binds archive when labels duplicate.

- path: environment/hold/CacheKeep.java
  kind: helper
  rhymes_with: op_b
  non_fix_purpose: Extends PIN login markers indefinitely for offline tooling; never refreshes session lineage for runtime.
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [Java, host, software, PKCS, module, slots, slot, token, key, rotation, restore, drills, signing, verify, calls, offline, object, scan, live, crypto, work, wrong, PIN, cached, sessions, session, policy, findscan, matching, counts, auth, stub, fixtures, seed, output, version, array, role, archive, provider_bound, pin_fresh, ttl_sec, certs, cert, label, handle_valid, runtime, authorization, identity, presence, rebind]
```
