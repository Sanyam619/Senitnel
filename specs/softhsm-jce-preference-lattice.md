### Decision
GO — Attempt 1. Security-category SoftHSM-backed JCE preference lattice across C JNI pack/mode, Java revoke/window, and durable keystore root under a sealed expected fingerprint; opaque symbols; surfcheck false-green; no repair/debug framing; no SealExpect calculator.

### Metadata
- version: 2
- Task name: softhsm-jce-preference-lattice
- Title: SoftHSM JCE Preference Lattice
- Category: security
- Languages: [Java, C]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: [tool_specific]
- Tags: [softhsm, jce, trust-authority, admission, revocation, attestation]
- Milestones: 0

## Authoring Brief

### Public contract

A local signing desk under `/app` uses SoftHSM-backed JCE after a provider-pack cutover. Surface probes green tokens while the sealed host gate rejects live sign and verify across several key generations. Provider order, mode bits, keystore generation binding, and revoke windows disagree on which root binds sessions and what admits.

Produce `/output/sign-ledger.json` covering every case under `/app/data/cases/`. The ledger needs:

- `schema_version` — fixed value `jce-desk-1`
- `rows` — array with `id`, `decision` (`accept` or `reject`), and `reason_code` on each row
- `bind_epoch` — equal to the `epoch` value in `/app/data/state/runtime.json`

Running `/app/scripts/desk-reload.sh` and then `/app/scripts/run-desk.sh` again must keep the same decisions and the same `bind_epoch`. The runtime epoch in `/app/data/state/runtime.json` must also stay put across that reload.

Reason vocabulary:

- Provider/mode pack refusals when surface OK used the wrong pack → `wrong_pack`
- Keystore generation mismatches across durable versus live roots → `root_skew`
- In-window revoked prior-generation material → `stale_slot`
- Current revocation outside that window → `revoked`
- Successful admit → `ok_bound`

Surface OK is not host authority. Leave `/app/bin/surfcheck`, `/app/scripts/run-desk.sh`, and `/app/data/cases/` in place and unmodified. Outputs must match a rebuild of the admit path under the sealed gate; hand-written stand-ins fail.

### Failure topology

Three authority splits interact. SoftHSM JNI pack rank and mode tags can disagree with leaf-surface OK, so cases that skim green still fail sealed host admit. Revoke marks plus a freshness window disagree with prior-generation local verify: admitting on surface alone reopens stale accept, while over-broad hard-block mislabels in-window cases. Durable keystore material under `data/roots/` disagrees with the live in-memory bundle after cutover: binding the wrong bundle flips accept/reject across desk-reload. The sealed gate rejects self-consistent preference digests that do not match its baked expected lattice fingerprint. Partial fixes that restore one cluster reopen another.

### Environment shape

- **`environment/native/`** — C SoftHSM JNI bridge (`knit_xv` pack/mode decision; `skim_xv` decoy).
- **`environment/nest/`** — Java revoke/window policy (`op_b`; `SkimY` decoy).
- **`environment/forge/`** — Java durable-root bind (`op_c`; `SkimZ` decoy).
- **`environment/flux/`** — Opaque preference sheets consumed by bridge and gate.
- **`environment/desk/` / `cmd/` / `lib/`** — Desk emit, signhold, holdrun entrypoints.
- **`environment/scripts/`** — run-desk, desk-reload, rebuild, surfcheck.
- **`environment/data/`** — cases, revoke marks/window, root bundles, token store, runtime state.
- **`environment/docs/`** — architecture notes (not the operational contract).
- Sealed gate jar installed under `/opt/desk/lib/gate.jar` (classpath ahead of rebuildable classes).

### Required artifacts

- `instruction.md` — symptoms-only public contract; no fix/repair/debug framing; no make recipe as primary activity.
- `task.toml` — category `security`; languages Java + C; `allow_internet = false`.
- `output_contract.toml` — ledger path and instruction-check tokens.
- `environment/Dockerfile` + `.dockerignore` — JDK + gcc/make + pytest pinned; SoftHSM bridge builds in-image; gate sealed at image build.
- `tests/test.sh` + `tests/test_outputs.py` — six hard outcome tests (re-invoke desk paths; no trivial existence-only checks).
- `solution/solve.sh` — rewrites the three decision bodies, rebuilds, runs desk.
- Full environment tree per Initial Draft Commitments (≥20 files excl. Docker files).

### Test plan

1. **test_q3_mica** — wrong SoftHSM pack/mode → `reject`/`wrong_pack` (not admit).
2. **test_w7_slate** — second wrong-pack generation → same reason (not scenario-specific).
3. **test_n2_basalt** — durable vs live root mismatch → `reject`/`root_skew`.
4. **test_k4_flint** — in-window revoked prior-gen → `reject`/`stale_slot` (not `revoked`/`ok_bound`).
5. **test_p9_shale** — out-of-window revoked → `reject`/`revoked` (not `stale_slot`/`ok_bound`).
6. **test_r6_chert** — schema + exact accept set (`ok_bound`) survive desk-reload + re-run; green `surfcheck` does not grant host admit; prohibited paths untouched; sealed gate ACCEPTs only tool-correct lattice.

Multiple internal orderings may pass if outcomes hold. Chain-dependent only on shared ledger emit (not on prior test mutation).

### Drafting guardrails

Instruction stays symptoms-only: no precedence recipes, no module hints, no "debug/fix/bug" framing, no leading "restore the Java project" / make checklist. Fix-path symbols use opaque names from the construction manifest only. Expected decisions live in test code (RC5). No SealExpect / preference calculator on the solver-visible classpath. Decoy skim modules must compile and serve real non-fix surface paths. Test names must not contain instruction nouns. CR8: no single file references more than two `symbol_table` symbols. Sealed gate jar must sit ahead of rebuildable classes so `make install` cannot replace the expect fingerprint.

### Triviality Ledger

- Surface-only admit passes green `surfcheck` but fails `wrong_pack` because JNI pack/mode never binds.
- Always-clear policy admits revoked material and fails `stale_slot`/`revoked` polarity.
- Live-bundle rebind may look correct pre-reload but fails `test_n2_basalt` / reload hold when durable disk root is authority.
- Hand-writing `/output/sign-ledger.json` or forging a self-consistent preference digest without repairing the tools fails sealed gate and re-invoked sign/hold/emit.
- Shipping a SealExpect-style calculator would collapse to PKCS#11-style forgery — blocked by baking opaque expected fingerprint into sealed gate only.

### Per-gate Pitfall Inventory

- **RC1**: Oracle must rewrite three decision bodies with real logic, not delete branches or flip a flag.
- **RC2**: No `broken_*`/`buggy_*`/`golden_*` in solver-visible paths or test names.
- **RC3**: Every case asserts decision + exact reason_code, not schema/existence alone.
- **RC4**: Expected map embedded in `test_outputs.py`; cases are not the answer key.
- **RC5**: No answer-shaped ledger under `environment/`.
- **RC6**: Instruction is symptoms-only; no authority precedence table or fix loci; soft rebuild language only.
- **RC7**: Oracle substantive LOC across C + Java ≥80 comfortable band.
- **GX1/GX3/GX9/GX10**: Opaque symbols; no answer recital of per-row triples in instruction; no polarity contradictions in one sentence.
- **CR8**: desk main / signhold / emit each name at most one fix-path symbol.
- **static checks**: `allow_internet = false`; pytest in Dockerfile; 20+ env files; `.dockerignore` present; security tags (`trust-authority`, `admission`, `revocation`).

### Initial Draft Commitments

- `environment/.dockerignore`
- `environment/Dockerfile`
- `environment/Makefile`
- `environment/include/desk_native.h`
- `environment/include/knit_xv.h`
- `environment/native/knit_xv.c`
- `environment/native/skim_xv.c`
- `environment/native/desk_jni.c`
- `environment/flux/PrefA.java`
- `environment/nest/OpB.java`
- `environment/nest/SkimY.java`
- `environment/nest/RowY.java`
- `environment/forge/OpC.java`
- `environment/forge/SkimZ.java`
- `environment/forge/RowZ.java`
- `environment/lib/NativeBridge.java`
- `environment/lib/JsonOut.java`
- `environment/lib/CaseIo.java`
- `environment/lib/Paths.java`
- `environment/lib/AssembleY.java`
- `environment/desk/DeskMain.java`
- `environment/cmd/signhold/Main.java`
- `environment/cmd/holdrun/Main.java`
- `environment/cmd/emitout/Main.java`
- `environment/scripts/run-desk.sh`
- `environment/scripts/desk-reload.sh`
- `environment/scripts/rebuild.sh`
- `environment/scripts/surfcheck`
- `environment/docs/architecture.md`
- `environment/docs/desk-notes.md`
- `environment/config/desk.toml`
- `environment/config/mode.toml`
- `environment/data/build_fixtures.sh`
- `environment/data/state/runtime.json`
- `environment/data/revoke/window.toml`
- `environment/data/revoke/marks.rl`
- `environment/data/roots/live.bundle`
- `environment/data/roots/disk.bundle`
- `environment/data/cases/q3.json`
- `environment/data/cases/w7.json`
- `environment/data/cases/n2.json`
- `environment/data/cases/k4.json`
- `environment/data/cases/p9.json`
- `environment/data/cases/r6.json`
- `environment/data/cases/m1.json`
- `environment/gate/GateSeal.java`
- `instruction.md`
- `task.toml`
- `output_contract.toml`
- `tests/test.sh`
- `tests/test_outputs.py`
- `solution/solve.sh`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: native/knit_xv.c
  symbol: knit_xv
  kind: function
  signature: int knit_xv(const struct row_x *a, struct slot_x *b)
  purpose: Fill pack_ok and mode_tag for one SoftHSM bridge row.

- path: nest/OpB.java
  symbol: op_b
  kind: function
  signature: static int op_b(RowY a, SlotY b)
  purpose: Fill policy code from marks and freshness bounds.

- path: forge/OpC.java
  symbol: op_c
  kind: function
  signature: static int op_c(RowZ a, SlotZ b)
  purpose: Resolve whether durable keystore generation lines up with the bound value.
```

#### flipping_point_contract

```
locations:
  - id: A
    path: native/knit_xv.c
    controls_tests: [test_q3_mica, test_w7_slate]
  - id: B
    path: nest/OpB.java
    controls_tests: [test_k4_flint, test_p9_shale]
  - id: C
    path: forge/OpC.java
    controls_tests: [test_n2_basalt, test_r6_chert]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: environment/native/skim_xv.c
  kind: helper
  rhymes_with: knit_xv
  non_fix_purpose: Leaf token rolling digest used by surfcheck; ignores pack/mode authority.

- path: environment/nest/SkimY.java
  kind: helper
  rhymes_with: op_b
  non_fix_purpose: Id-token surface probe for desk --surface; ignores marks/window.

- path: environment/forge/SkimZ.java
  kind: helper
  rhymes_with: op_c
  non_fix_purpose: Warm-cache signature probe during emit; not durable-root authority.
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [signing, desk, SoftHSM, JCE, provider-pack, cutover, surface, probes, tokens, sealed, host, gate, verify, generations, provider, order, mode, bits, keystore, generation, binding, revoke, windows, root, sessions, admits, ledger, cases, schema_version, jce-desk-1, rows, decision, accept, reject, reason_code, bind_epoch, epoch, runtime, decisions, desk-reload, run-desk, vocabulary, pack, refusals, wrong_pack, mismatches, durable, live, roots, root_skew, in-window, revoked, prior-generation, material, stale_slot, revocation, window, admit, ok_bound, authority, surfcheck, outputs, rebuild, path, stand-ins, sign, key, case]
```
