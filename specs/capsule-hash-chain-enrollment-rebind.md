### Decision
GO — Attempt 1. Security-category capsule hash-chain enrollment rebind across C tip continuity, Rust revoke/freshness gate, and Go durable-root rebind; opaque symbols; surfcheck false-green bait; no debugging/segfault framing.

### Metadata
- version: 2
- Task name: capsule-hash-chain-enrollment-rebind
- Title: Capsule Hash-Chain Enrollment Rebind
- Category: security
- Languages: [C, Rust, Go]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: [tool_specific]
- Tags: [capsules, enrollment, revocation, hash-chain, rust, go]
- Milestones: 0

## Authoring Brief

### Public contract

Device update capsules under `/app` enroll through a C/Rust/Go stack after a key rotation and a partial revoke. Some capsules still look good on a local check but enrollment refuses them after a host reload. Sibling devices sometimes disagree on the same capsule family. `/app/bin/surfcheck` often reports OK when the enrollment path later rejects (or the reverse).

Produce `/output/enroll-ledger.json` covering every scenario under `/app/data/scenarios/`. The ledger needs:

- `schema_version` — fixed value `capsule-enroll-1`
- `cases` — array with `id`, `device_id`, `decision` (`accept` or `reject`), and `reason_code` on each row
- `reload_epoch` — equal to the `epoch` value in `/app/data/state/runtime.json`

Running `/app/scripts/host-reload.sh` and then `/app/scripts/run-enroll.sh` again must keep the same decisions and the same `reload_epoch`. The runtime epoch in `/app/data/state/runtime.json` must also stay put across that reload.

Reason vocabulary:

- Refresh-window refusals of material that verified under a prior generation but is current-revoked → `stale_chain`
- Current revocation outside that window → `revoked`
- Generation mismatch across sibling devices → `gen_skew`
- Successful enrollment → `ok_bound`

Signature-only surface OK is not enrollment authority. Leave `/app/bin/surfcheck`, `/app/scripts/run-enroll.sh`, and `/app/data/scenarios/` in place and unmodified. Rebuild with `make`, then run `/app/scripts/run-enroll.sh`.

### Failure topology

Three authority splits interact. Tip continuity on the framed capsule can disagree with leaf-signature surface OK, so siblings on the same family can diverge even when `surfcheck` is green. Revoke marks plus a freshness window disagree with prior-generation local verify: admitting on signature alone reopens stale-accept, while over-broad hard-block mislabels in-window cases. Durable root material under `data/roots/` disagrees with the live in-memory bundle after rotation: binding the wrong bundle makes accept/reject flip across host reload. Partial fixes that restore one cluster reopen another (stale accept vs fresh reject vs sibling skew vs reload drift).

### Environment shape

- **`environment/frame/`** — C framing tool (`framectl`); tip continuity decision and leaf-surface skim decoy.
- **`environment/policy/`** — Rust policy gate (`polgate`); revoke/freshness decision and surface skim decoy.
- **`environment/enroll/`** — Go enrollment CLI (`enrollctl`); durable-root rebind and ledger emit; warm-cache skim decoy.
- **`environment/scripts/`** — run-enroll, host-reload, rebuild-tools, surfcheck entrypoints.
- **`environment/data/`** — capsules, scenarios, revoke marks/window, root bundles, runtime state.
- **`environment/docs/`** — architecture and ledger notes (not the operational contract).
- **`environment/include/`** — shared C headers.

### Required artifacts

- `instruction.md` — symptoms-only public contract; no fix/repair/debug framing.
- `task.toml` — category `security`; languages C/Rust/Go; `allow_internet = false`.
- `output_contract.toml` — ledger path and instruction-check tokens.
- `environment/Dockerfile` + `.dockerignore` — toolchains + pytest pinned; project builds in-image.
- `tests/test.sh` + `tests/test_outputs.py` — six hard outcome tests (no trivial existence-only checks).
- `solution/solve.sh` — rewrites the three decision bodies, rebuilds, runs enroll.
- Full environment tree per Initial Draft Commitments (≥20 files excl. Docker files).

### Test plan

1. **test_m8_obsidian** — mismatched sibling tip → `reject`/`gen_skew` (not admit).
2. **test_p7_garnet** — second mismatched sibling → same reason (not scenario-specific).
3. **test_n4_topaz** — in-window revoked prior-gen → `reject`/`stale_chain` (not `revoked`/`ok_bound`).
4. **test_k9_onyx** — out-of-window revoked → `reject`/`revoked` (not `stale_chain`/`ok_bound`).
5. **test_r1_amber** — decisions, reason codes, ledger reload_epoch, and runtime epoch survive host-reload + re-enroll.
6. **test_t6_zircon** — schema + exact accept set (`ok_bound`) while green `surfcheck` does not grant enrollment; prohibited paths untouched.

Multiple internal orderings may pass if outcomes hold. Chain-dependent only on shared ledger emit (not on prior test mutation).

### Drafting guardrails

Instruction stays symptoms-only: no precedence recipes, no module hints, no "debug/fix/bug" framing. Fix-path symbols use opaque names from the construction manifest only. Expected decisions live in test code (RC5). Decoy `skim_*` modules must compile and serve real non-fix surface paths. Test names must not contain instruction nouns. CR8: no single file references more than two `symbol_table` symbols.

### Triviality Ledger

- Tip-only (signature) admit passes green `surfcheck` but fails sibling `gen_skew` tests because parent/anchor continuity never binds.
- Always-clear policy admits revoked material and fails `stale_chain`/`revoked` polarity.
- Live-bundle rebind may look correct pre-reload after promoting roots by hand but fails `test_r1_amber` when durable disk root is the authority that must survive reload.
- Hand-writing `/output/enroll-ledger.json` without repairing the tools fails reload hold and prohibited-path checks once the verifier re-runs enroll from built binaries.

### Per-gate Pitfall Inventory

- **RC1**: Oracle must rewrite three decision bodies with real logic, not delete branches or flip a flag.
- **RC2**: No `broken_*`/`buggy_*`/`golden_*` in solver-visible paths or test names.
- **RC3**: Every case asserts decision + exact reason_code, not schema/existence alone.
- **RC4**: Expected map embedded in `test_outputs.py`; scenarios are not the answer key.
- **RC5**: No answer-shaped ledger under `environment/`.
- **RC6**: Instruction is symptoms-only; no authority precedence table or fix loci.
- **RC7**: Oracle substantive LOC across three languages ≥80 comfortable band.
- **GX1/GX3/GX9/GX10**: Opaque symbols; no answer recital of per-row triples in instruction; no polarity contradictions in one sentence.
- **CR8**: `frame_main` / `polgate` main / `emit.go` each name at most one fix-path symbol.
- **static checks**: `allow_internet = false`; pytest in Dockerfile; 20+ env files; `.dockerignore` present.

### Initial Draft Commitments

- `environment/.dockerignore`
- `environment/Dockerfile`
- `environment/Makefile`
- `environment/include/frame.h`
- `environment/include/wire.h`
- `environment/frame/fold_q.h`
- `environment/frame/fold_q.c`
- `environment/frame/skim_frame.h`
- `environment/frame/skim_frame.c`
- `environment/frame/frame_main.c`
- `environment/policy/Cargo.toml`
- `environment/policy/Cargo.lock`
- `environment/policy/src/lib.rs`
- `environment/policy/src/gate_r.rs`
- `environment/policy/src/skim_pol.rs`
- `environment/policy/src/main.rs`
- `environment/enroll/go.mod`
- `environment/enroll/cmd/enrollctl/main.go`
- `environment/enroll/internal/slot_w.go`
- `environment/enroll/internal/skim_en.go`
- `environment/enroll/internal/emit.go`
- `environment/scripts/run-enroll.sh`
- `environment/scripts/host-reload.sh`
- `environment/scripts/rebuild-tools.sh`
- `environment/scripts/surfcheck`
- `environment/docs/architecture.md`
- `environment/docs/enroll-schema.md`
- `environment/data/state/runtime.json`
- `environment/data/roots/live.bundle`
- `environment/data/roots/disk.bundle`
- `environment/data/revoke/current.rl`
- `environment/data/revoke/window.toml`
- `environment/data/capsules/cap_m2.bin`
- `environment/data/capsules/cap_w2.bin`
- `environment/data/capsules/cap_q3.bin`
- `environment/data/capsules/cap_k9.bin`
- `environment/data/capsules/cap_n4.bin`
- `environment/data/capsules/cap_p7.bin`
- `environment/data/capsules/cap_t1.bin`
- `environment/data/scenarios/m2.json`
- `environment/data/scenarios/w2.json`
- `environment/data/scenarios/q3.json`
- `environment/data/scenarios/k9.json`
- `environment/data/scenarios/n4.json`
- `environment/data/scenarios/p7.json`
- `environment/data/scenarios/t1.json`
- `instruction.md`
- `task.toml`
- `output_contract.toml`
- `tests/test.sh`
- `tests/test_outputs.py`
- `solution/solve.sh`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: frame/fold_q.c
  symbol: fold_q
  kind: function
  signature: int fold_q(const struct row_q *a, struct slot_q *b)
  purpose: Populate tip_ok/sig_ok/gen for one framed row against the supplied anchor.

- path: policy/src/gate_r.rs
  symbol: gate_r
  kind: function
  signature: pub fn gate_r(a: &RowR, b: &mut SlotR) -> i32
  purpose: Populate policy code for one row from marks and freshness bounds.

- path: enroll/internal/slot_w.go
  symbol: slot_w
  kind: function
  signature: func slot_w(a RowW, b *SlotW) error
  purpose: Resolve whether the durable root generation lines up with the bound value.
```

#### flipping_point_contract

```
locations:
  - id: A
    path: frame/fold_q.c
    controls_tests: [test_m8_obsidian, test_p7_garnet]
  - id: B
    path: policy/src/gate_r.rs
    controls_tests: [test_n4_topaz, test_k9_onyx]
  - id: C
    path: enroll/internal/slot_w.go
    controls_tests: [test_r1_amber, test_t6_zircon]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: environment/frame/skim_frame.c
  kind: helper
  rhymes_with: fold_q
  non_fix_purpose: Leaf-surface rolling hash used by framectl skim / surfcheck.

- path: environment/policy/src/skim_pol.rs
  kind: helper
  rhymes_with: gate_r
  non_fix_purpose: Id-token surface probe for polgate --surface; ignores marks/window.

- path: environment/enroll/internal/skim_en.go
  kind: helper
  rhymes_with: slot_w
  non_fix_purpose: Warm-cache signature probe called during enroll; not durable-root authority.
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [device, update, capsules, stack, key, rotation, partial, revoke, check, enrollment, host, reload, sibling, devices, capsule, family, surfcheck, scenarios, ledger, schema_version, cases, device_id, decision, accept, reject, reason_code, reload_epoch, epoch, runtime, decisions, refusals, material, generation, stale_chain, revocation, window, revoked, mismatch, gen_skew, signature, surface, authority, make]
```
