### Decision
GO — Redesign. Security ops cutover (no app-source repair): correct Go/Java engines; mid-cutover trust STATE; agent runs bundlepub/tmrebind/tickgate then probe; hard scenarios include root-scoped SPI, warm-cache intermediate pin, ticket floor, not_before skew.

### Metadata
- version: 2
- Task name: workload-svid-trust-mesh-cutover
- Title: Workload SVID Trust-Mesh Cutover
- Category: security
- Languages: ["Go", "Java"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: []
- Tags: ["spiffe", "svid", "mtls", "trust-manager", "go", "java"]
- Milestones: 0

## Authoring Brief

### Public contract

A single-container mesh lab under `/app/` is mid-cutover between Go Workload API SVID issuance and Java services that authenticate peers through KeyStore/TrustManager material plus a custom SPI. Surface readiness still prints OK while some RPCs succeed on a fresh connection, some fail only after the same connection is reused, and some still accept chains whose intermediate has already expired when the JVM keeps a stale TrustManager.

**Symptoms the agent sees (instruction.md level):**
- Readiness prints OK.
- Fresh connections and reused connections disagree.
- Expired intermediates can still be accepted under a stale TrustManager.
- Updating a CA file alone is insufficient.

**Required outcomes:**
- `/output/mesh-cutover.json` exists with `schema_version` `mesh-cutover-1`, integer `epoch` matching `/app/data/state/runtime.json`, and a `cases` array covering every scenario under `/app/data/scenarios/`.
- Each case has string `id`, string `decision` (`accept` or `reject`), string `reason_code`, string `handshake` (`fresh` or `resumed`), and integer `trust_epoch`.
- Per-scenario required values match `/app/ops/mesh-notes.toml`.
- Report must come from a real `/app/bin/meshctl probe` run, not a hand-written stand-in.
- Fixtures under `/app/data/fixtures/` unchanged.

**Constraints:**
- `[environment] allow_internet = false`; verifier deps in Dockerfile.
- No multi-container layout.
- No repair/debug framing in instruction — cutover/trust-mesh alignment only.
- Languages: Go + Java.

### Failure topology

Three interacting cutover remnants. First, issuance still binds the pre-cutover root because the live bundle epoch is not published — CA PEM side copies look fine while new SVIDs remain on the wrong root. Second, Java TrustManager/SPI keeps a cached manager that accepts expired intermediates until rebuilt from the live bundle. Third, session tickets from the prior epoch resume without re-validation, so reuse paths diverge from fresh handshakes. False-green `readycheck` only curls readiness and ignores probe truth.

Hard because Go and Java refresh on different clocks/paths; no single CA update or TrustManager flush alone clears all scenario rows.

### Environment shape

- `environment/Dockerfile` + `.dockerignore` — Go 1.24 bookworm + OpenJDK 17, pytest; offline image.
- `environment/k9/` — Go `fold_a` live-bundle publish + `fold_legacy` decoy.
- `environment/m2/` — Java `sieve_b` trust decision + `sieve_preview` decoy.
- `environment/p7/` — Go `emit_c` ticket gate + ledger emit + `emit_dry` decoy.
- `environment/tools/` — `meshctl`, `readycheck`.
- `environment/ops/` — mesh-notes, runbook fragments.
- `environment/config/` — profiles / field notes.
- `environment/data/` — scenarios, state, fixtures, material.

### Required artifacts

- `tasks/workload-svid-trust-mesh-cutover/task.toml` with `allow_internet = false`, `category = "security"`.
- `instruction.md` — symptoms-only cutover prose (not repair/debug).
- `tests/test.sh`, `tests/test_outputs.py` — six opaque hard tests.
- `solution/solve.sh` — oracle patches ≥3 loci (≥30 LOC substantive) then meshctl probe.
- `environment/**` — 25+ non-Docker files per Initial Draft Commitments.

### Test plan

- `test_k9_zircon` — fresh legitimate SVID under active root accepts with notes reason_code.
- `test_m2_quartz` — resumed pre-cutover ticket rejects after epoch flip.
- `test_n3_garnet` — expired intermediate rejects even when cache was warm.
- `test_p7_topaz` — post-flip dual-root legacy peer rejects under current epoch.
- `test_r8_onyx` — accept cases bind SPIFFE/SPI subject consistently with notes.
- `test_t1_amber` — ledger schema/epoch/all cases present; fixtures untouched.

Multiple valid internal orderings may pass if outcomes match notes. Chain-dependent: field tests need a successful meshctl probe.

### Drafting guardrails

Do not embed instruction nouns in fix-path symbols, parameters, or test names. Instruction may use standard SPIFFE/SVID/TrustManager language. No repair/debug TODOs. readycheck must genuinely implement shallow readiness. No HINT walkthroughs under environment/. Do not create `environment/bin/` (package hygiene); install meshctl to `/app/bin` from `tools/` in the Dockerfile.

### Triviality Ledger

- Calling fold_legacy (CA PEM copy) passes readycheck but fails fresh-root and dual-root tests because live-bundle epoch stays stale.
- Rebuilding TrustManager without fold_a leaves issuance on pre-cutover root → test_k9_zircon / test_p7_topaz fail.
- Publishing live bundle without sieve_b leaves expired-intermediate accepts → test_n3_garnet fails.
- Gating tickets without emit_c ledger write fails test_t1_amber / test_m2_quartz.
- Hand-writing mesh-cutover.json without meshctl probe fails verifier rebuild/probe equality checks.

### Per-gate Pitfall Inventory

- RC1: Oracle adds substantive logic in three modules — never delete-bug or wholesale restore golden.
- RC3: Tests assert per-scenario decisions/reason_codes/handshake — not mere file existence.
- RC5: Expected decisions live in mesh-notes + test code, not golden under environment/answer paths.
- RC6: Instruction symptoms-only — no fold_a / sieve_b / emit_c order.
- RC7: solve.sh non-boilerplate ≥30 LOC.
- CR1/CR2: Construction manifest symbols verbatim; 2+2+2 flip split.
- CR7/GX9: JSON field names in instruction; exact scenario values only in mesh-notes/tests.
- Static: allow_internet=false, .dockerignore, absolute paths, category security, Go+Java.

### Initial Draft Commitments

- `tasks/workload-svid-trust-mesh-cutover/task.toml`
- `tasks/workload-svid-trust-mesh-cutover/instruction.md`
- `tasks/workload-svid-trust-mesh-cutover/output_contract.toml`
- `tasks/workload-svid-trust-mesh-cutover/tests/test.sh`
- `tasks/workload-svid-trust-mesh-cutover/tests/test_outputs.py`
- `tasks/workload-svid-trust-mesh-cutover/solution/solve.sh`
- `tasks/workload-svid-trust-mesh-cutover/environment/Dockerfile`
- `tasks/workload-svid-trust-mesh-cutover/environment/.dockerignore`
- `tasks/workload-svid-trust-mesh-cutover/environment/go.mod`
- `tasks/workload-svid-trust-mesh-cutover/environment/go.sum`
- `tasks/workload-svid-trust-mesh-cutover/environment/k9/fold_a.go`
- `tasks/workload-svid-trust-mesh-cutover/environment/k9/fold_legacy.go`
- `tasks/workload-svid-trust-mesh-cutover/environment/k9/api.go`
- `tasks/workload-svid-trust-mesh-cutover/environment/k9/doc.go`
- `tasks/workload-svid-trust-mesh-cutover/environment/p7/emit_c.go`
- `tasks/workload-svid-trust-mesh-cutover/environment/p7/emit_dry.go`
- `tasks/workload-svid-trust-mesh-cutover/environment/p7/api.go`
- `tasks/workload-svid-trust-mesh-cutover/environment/p7/doc.go`
- `tasks/workload-svid-trust-mesh-cutover/environment/cmd/meshprobe/main.go`
- `tasks/workload-svid-trust-mesh-cutover/environment/m2/pom.xml`
- `tasks/workload-svid-trust-mesh-cutover/environment/m2/src/main/java/io/helix/qx/sieve_b.java`
- `tasks/workload-svid-trust-mesh-cutover/environment/m2/src/main/java/io/helix/qx/sieve_preview.java`
- `tasks/workload-svid-trust-mesh-cutover/environment/m2/src/main/java/io/helix/qx/SpiGate.java`
- `tasks/workload-svid-trust-mesh-cutover/environment/m2/src/main/java/io/helix/qx/CacheView.java`
- `tasks/workload-svid-trust-mesh-cutover/environment/m2/src/main/java/io/helix/qx/SieveMain.java`
- `tasks/workload-svid-trust-mesh-cutover/environment/data/material/ca-side.pem`
- `tasks/workload-svid-trust-mesh-cutover/environment/tools/meshctl`
- `tasks/workload-svid-trust-mesh-cutover/environment/tools/readycheck`
- `tasks/workload-svid-trust-mesh-cutover/environment/ops/mesh-notes.toml`
- `tasks/workload-svid-trust-mesh-cutover/environment/ops/runbook-ready.md`
- `tasks/workload-svid-trust-mesh-cutover/environment/config/profiles/field.toml`
- `tasks/workload-svid-trust-mesh-cutover/environment/config/profiles/fleet.toml`
- `tasks/workload-svid-trust-mesh-cutover/environment/config/field-notes.md`
- `tasks/workload-svid-trust-mesh-cutover/environment/data/state/runtime.json`
- `tasks/workload-svid-trust-mesh-cutover/environment/data/state/live-bundle.json`
- `tasks/workload-svid-trust-mesh-cutover/environment/data/state/tm-cache.json`
- `tasks/workload-svid-trust-mesh-cutover/environment/data/scenarios/fresh_ok.json`
- `tasks/workload-svid-trust-mesh-cutover/environment/data/scenarios/resume_stale.json`
- `tasks/workload-svid-trust-mesh-cutover/environment/data/scenarios/expired_inter.json`
- `tasks/workload-svid-trust-mesh-cutover/environment/data/scenarios/dual_post.json`
- `tasks/workload-svid-trust-mesh-cutover/environment/data/scenarios/spi_bind.json`
- `tasks/workload-svid-trust-mesh-cutover/environment/data/fixtures/seed.json`
- `tasks/workload-svid-trust-mesh-cutover/environment/data/material/roots.json`
- `tasks/workload-svid-trust-mesh-cutover/environment/data/material/tickets.json`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: environment/k9/fold_a.go
  symbol: fold_a
  kind: function
  signature: func fold_a(a string, b string) error
  purpose: Writes live-bundle.json active root and epoch used by issuance probes.

- path: environment/m2/src/main/java/io/helix/qx/sieve_b.java
  symbol: sieve_b
  kind: class
  signature: static String apply(String a, String b)
  purpose: Rebuilds trust decision from live bundle and chain material, clearing stale cache when needed.

- path: environment/p7/emit_c.go
  symbol: emit_c
  kind: function
  signature: func emit_c(a string, b string) error
  purpose: Gates resumed tickets against live epoch and writes mesh-cutover.json cases.
```

#### flipping_point_contract

```
locations:
  - id: A
    path: environment/k9/fold_a.go
    controls_tests: [test_k9_zircon, test_p7_topaz]
  - id: B
    path: environment/m2/src/main/java/io/helix/qx/sieve_b.java
    controls_tests: [test_n3_garnet, test_r8_onyx]
  - id: C
    path: environment/p7/emit_c.go
    controls_tests: [test_m2_quartz, test_t1_amber]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: environment/k9/fold_legacy.go
  kind: helper
  rhymes_with: fold_a
  non_fix_purpose: Copies CA PEM into a side path for ops dry-runs without publishing live-bundle epoch.

- path: environment/m2/src/main/java/io/helix/qx/sieve_preview.java
  kind: helper
  rhymes_with: sieve_b
  non_fix_purpose: Lists KeyStore aliases for diagnostics without rebuilding TrustManager or clearing cache.

- path: environment/p7/emit_dry.go
  kind: helper
  rhymes_with: emit_c
  non_fix_purpose: Pretty-prints probe plan without gating tickets or writing the cutover ledger.
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [mesh, cutover, Workload, API, SVID, issuance, Go, side, Java, services, peers, KeyStore, TrustManager, material, custom, SPI, Surface, readiness, RPCs, connection, chains, intermediate, JVM, stale, refresh, session, reuse, agreement, meshctl, probe, output, notes, ops, scenario, scenarios, data, report, stand-in, fixtures, schema_version, epoch, state, runtime, cases, array, id, decision, accept, reject, reason_code, handshake, fresh, resumed, trust_epoch, values]
```
