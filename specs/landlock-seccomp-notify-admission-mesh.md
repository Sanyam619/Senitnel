### Decision
GO — Attempt 1. Security admission mesh across Go durable path-identity fold, C seccomp-notify sieve, and Go FD/revoke emit; opaque symbols; surfcheck false-green; sealed EXPECTED; no repair/debug framing.

### Metadata
- version: 2
- Task name: landlock-seccomp-notify-admission-mesh
- Title: Landlock Seccomp Admission Mesh
- Category: security
- Languages: [Go, C]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: [tool_specific]
- Tags: [admission, quarantine, landlock, seccomp-notify, path-identity, trust-authority]
- Milestones: 0

## Authoring Brief

### Public contract

A local job broker applies filesystem access rules and syscall notify decisions for open and exec. After a mesh refresh, some jobs pass a surface probe while the host quarantine ledger disagrees on path identity, file-descriptor inheritance, and notify allow or deny across reload epochs.

Produce `/output/admit-ledger.json` covering every scenario under `/app/data/scenarios/`. The ledger needs:

- `schema_version` — fixed value `admit-mesh-1`
- `cases` — array with `id`, `job_id`, `decision` (`accept` or `quarantine`), and `reason_code` on each row
- `reload_epoch` — equal to the `epoch` value in `/app/data/state/runtime.json`

Running `/app/scripts/mesh-refresh.sh` and then `/app/scripts/run-admit.sh` again must keep the same decisions and the same `reload_epoch`. The runtime epoch in `/app/data/state/runtime.json` must also stay put across that refresh.

Reason vocabulary:

- Durable path identity outside the allow set → `path_drift`
- Inherited descriptor behind the current epoch → `fd_stale`
- Notify allow/deny disagreeing with filesystem rules under durable identity (including exec hold) → `notify_skew`
- Marked material inside the refresh revoke window → `epoch_revoke`
- Successful admission → `ok_admit`

A surface probe that reports OK is not host admission authority. Leave `/app/bin/surfcheck`, `/app/scripts/run-admit.sh`, and `/app/data/scenarios/` in place and unmodified. Outputs must match a rebuild of the admission path; hand-written stand-ins fail.

### Failure topology

Three authority splits interact. Path identity can resolve live aliases (symlink/bind decoys) that disagree with the durable root Landlock allow set, so surface lexical OK admits jobs the host must quarantine as `path_drift`. Seccomp-notify decisions can allow open/exec independently of that Landlock durable verdict — including exec-hold lanes — producing `notify_skew` when only one side is corrected. FD inheritance and revoke-window marks couple into ledger emit across mesh refresh: ignoring `fd_epoch` or binding live runtime flips accept/quarantine and drifts `reload_epoch`. Partial Landlock-only or notify-only patches reopen distant scenario classes.

### Environment shape

- **`environment/qx/`** — Go policy broker (`meshctl`); durable path fold, ledger emit, lexical skim decoy.
- **`environment/rz/`** — C notify helper (`nhelper`); sieve decision and always-allow skim decoy.
- **`environment/scripts/`** — run-admit, mesh-refresh, rebuild-tools, surfcheck entrypoints.
- **`environment/data/`** — scenarios, root maps (durable/live), allow list, revoke window, runtime state, job fixtures.
- **`environment/docs/`** — architecture notes (not the operational contract).
- **`environment/include/`** — shared C headers.
- **`environment/config/`** — field notes without precedence recipes.

### Required artifacts

- `instruction.md` — symptoms-only public contract; no fix/repair/debug framing; no make recipe as the task.
- `task.toml` — category `security`; languages Go/C; `allow_internet = false`.
- `output_contract.toml` — ledger path and instruction-check tokens.
- `environment/Dockerfile` + `.dockerignore` — Go+GCC + pytest pinned; project builds in-image.
- `tests/test.sh` + `tests/test_outputs.py` — seven hard outcome tests (no trivial existence-only checks).
- `solution/solve.sh` — rewrites three decision bodies, rebuilds, runs admit.
- Full environment tree per Initial Draft Commitments (≥20 files excl. Docker files).

### Test plan

1. **test_m8_obsidian** — symlink alias whose durable identity is allowed → `accept`/`ok_admit`.
2. **test_k3_garnet** — bind-mount decoy into vault on live map but durable outside allow → `quarantine`/`path_drift`.
3. **test_n4_topaz** — vault path with `fd_epoch` behind runtime → `quarantine`/`fd_stale`.
4. **test_p7_onyx** — exec with hold wire where open would pass Landlock → `quarantine`/`notify_skew`.
5. **test_q7_amber** — marked in revoke window → `quarantine`/`epoch_revoke`.
6. **test_r1_zircon** — decisions, reason codes, ledger reload_epoch, and runtime epoch survive mesh-refresh + re-admit; schema holds.
7. **test_t6_jade** — clean open admit (`ok_admit`) while green surfcheck on a quarantined id does not grant host admission.

Multiple internal orderings may pass if outcomes hold. Chain-dependent only on shared ledger emit (not on prior test mutation).

### Drafting guardrails

Instruction stays symptoms-only: no precedence recipes, no module hints, no repair/debug/bug framing, no leading make/cargo lines. Fix-path symbols use opaque names from the construction manifest only. Expected decisions live in test code (RC5). Decoy skim modules must compile and serve real non-fix surface paths. Test names must not contain instruction nouns. CR8: no single file references more than two `symbol_table` symbols.

### Triviality Ledger

- Lexical/live-map fold passes green surfcheck and may admit bind decoys → fails `test_k3_garnet` / wrong `test_m8_obsidian`.
- Notify always-allow (or landlock-ignore) admits exec-hold → fails `test_p7_onyx`.
- Emit ignoring fd_epoch or revoke window mislabels `fd_stale`/`epoch_revoke` and breaks reload hold → fails `test_n4_topaz` / `test_q7_amber` / `test_r1_zircon`.
- Hand-writing `/output/admit-ledger.json` without repairing tools fails reload hold and prohibited-path checks once the verifier re-runs admit from built binaries.

### Per-gate Pitfall Inventory

- **RC1**: Oracle must rewrite three decision bodies with real logic, not delete branches or flip a flag.
- **RC2**: No `broken_*`/`buggy_*`/`golden_*` in solver-visible paths or test names.
- **RC3**: Every case asserts decision + exact reason_code, not schema/existence alone.
- **RC4**: Expected map embedded in `test_outputs.py`; scenarios are not the answer key.
- **RC5**: No answer-shaped ledger under `environment/`.
- **RC6**: Instruction is symptoms-only; no authority precedence table or fix loci; no make-as-task.
- **RC7**: Oracle substantive LOC across Go+C ≥80 comfortable band.
- **GX1/GX3/GX9/GX10**: Opaque symbols; no answer recital of per-row triples in instruction; no polarity contradictions in one sentence.
- **CR8**: meshctl main / nhelper main / emit each name at most one fix-path symbol (distribute).
- **category_classifier**: Lead with admit/quarantine outcomes and surface≠authority; tags trust/admission flavored; soft rebuild note only.
- **static checks**: `allow_internet = false`; pytest in Dockerfile; 20+ env files; `.dockerignore` present.

### Initial Draft Commitments

- `tasks/landlock-seccomp-notify-admission-mesh/task.toml`
- `tasks/landlock-seccomp-notify-admission-mesh/instruction.md`
- `tasks/landlock-seccomp-notify-admission-mesh/output_contract.toml`
- `tasks/landlock-seccomp-notify-admission-mesh/construction_manifest.json`
- `tasks/landlock-seccomp-notify-admission-mesh/tests/test.sh`
- `tasks/landlock-seccomp-notify-admission-mesh/tests/test_outputs.py`
- `tasks/landlock-seccomp-notify-admission-mesh/solution/solve.sh`
- `tasks/landlock-seccomp-notify-admission-mesh/environment/Dockerfile`
- `tasks/landlock-seccomp-notify-admission-mesh/environment/.dockerignore`
- `tasks/landlock-seccomp-notify-admission-mesh/environment/Makefile`
- `tasks/landlock-seccomp-notify-admission-mesh/environment/include/wire.h`
- `tasks/landlock-seccomp-notify-admission-mesh/environment/rz/sieve_b.h`
- `tasks/landlock-seccomp-notify-admission-mesh/environment/rz/sieve_b.c`
- `tasks/landlock-seccomp-notify-admission-mesh/environment/rz/skim_sieve.h`
- `tasks/landlock-seccomp-notify-admission-mesh/environment/rz/skim_sieve.c`
- `tasks/landlock-seccomp-notify-admission-mesh/environment/rz/notify_main.c`
- `tasks/landlock-seccomp-notify-admission-mesh/environment/qx/go.mod`
- `tasks/landlock-seccomp-notify-admission-mesh/environment/qx/cmd/meshctl/main.go`
- `tasks/landlock-seccomp-notify-admission-mesh/environment/qx/internal/fold_a.go`
- `tasks/landlock-seccomp-notify-admission-mesh/environment/qx/internal/emit_c.go`
- `tasks/landlock-seccomp-notify-admission-mesh/environment/qx/internal/skim_fold.go`
- `tasks/landlock-seccomp-notify-admission-mesh/environment/qx/internal/io_util.go`
- `tasks/landlock-seccomp-notify-admission-mesh/environment/scripts/run-admit.sh`
- `tasks/landlock-seccomp-notify-admission-mesh/environment/scripts/mesh-refresh.sh`
- `tasks/landlock-seccomp-notify-admission-mesh/environment/scripts/rebuild-tools.sh`
- `tasks/landlock-seccomp-notify-admission-mesh/environment/scripts/surfcheck`
- `tasks/landlock-seccomp-notify-admission-mesh/environment/docs/architecture.md`
- `tasks/landlock-seccomp-notify-admission-mesh/environment/config/field-notes.md`
- `tasks/landlock-seccomp-notify-admission-mesh/environment/data/state/runtime.json`
- `tasks/landlock-seccomp-notify-admission-mesh/environment/data/roots/durable.map`
- `tasks/landlock-seccomp-notify-admission-mesh/environment/data/roots/live.map`
- `tasks/landlock-seccomp-notify-admission-mesh/environment/data/w1/allow.list`
- `tasks/landlock-seccomp-notify-admission-mesh/environment/data/revoke/window.toml`
- `tasks/landlock-seccomp-notify-admission-mesh/environment/data/scenarios/m2.json`
- `tasks/landlock-seccomp-notify-admission-mesh/environment/data/scenarios/w2.json`
- `tasks/landlock-seccomp-notify-admission-mesh/environment/data/scenarios/k9.json`
- `tasks/landlock-seccomp-notify-admission-mesh/environment/data/scenarios/n4.json`
- `tasks/landlock-seccomp-notify-admission-mesh/environment/data/scenarios/p7.json`
- `tasks/landlock-seccomp-notify-admission-mesh/environment/data/scenarios/q3.json`
- `tasks/landlock-seccomp-notify-admission-mesh/environment/data/scenarios/t1.json`
- `tasks/landlock-seccomp-notify-admission-mesh/environment/data/fixtures/seed.json`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: qx/internal/fold_a.go
  symbol: fold_a
  kind: function
  signature: func fold_a(a rowA, b *slotA) error
  purpose: Resolve request path through root maps into canonical identity and allow-bit.

- path: rz/sieve_b.c
  symbol: sieve_b
  kind: function
  signature: int sieve_b(int a, const char *b, const char *c)
  purpose: Return notify allow/deny from landlock bit, op token, and wire token.

- path: qx/internal/emit_c.go
  symbol: emit_c
  kind: function
  signature: func emit_c(a rowC, b *slotC) error
  purpose: Fold FD/revoke/landlock/notify bits into decision, reason, and reload epoch.
```

#### flipping_point_contract

```
locations:
  - id: A
    path: qx/internal/fold_a.go
    controls_tests: [test_m8_obsidian, test_k3_garnet]
  - id: B
    path: rz/sieve_b.c
    controls_tests: [test_p7_onyx, test_t6_jade]
  - id: C
    path: qx/internal/emit_c.go
    controls_tests: [test_n4_topaz, test_q7_amber, test_r1_zircon]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: qx/internal/skim_fold.go
  kind: helper
  rhymes_with: fold_a
  non_fix_purpose: Lexical path presence skim used by surfcheck; ignores durable maps.

- path: notify/skim_sieve.c
  kind: helper
  rhymes_with: sieve_b
  non_fix_purpose: Surface notify always-allow helper for probe path; not host authority.
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [job, broker, filesystem, access, rules, syscall, notify, open, exec, mesh, refresh, jobs, surface, probe, host, quarantine, ledger, path, identity, descriptor, inheritance, allow, deny, reload, epochs, scenarios, decision, accept, reason_code, reload_epoch, epoch, runtime, path_drift, fd_stale, notify_skew, epoch_revoke, ok_admit, admission, authority, landlock, seccomp]
```
