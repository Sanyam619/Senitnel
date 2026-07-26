### Decision
GO — Attempt 1. Security admission mesh across Go durable path-identity fold, C seccomp-notify sieve, and Go FD/revoke emit; opaque symbols; surfcheck false-green; sealed EXPECTED; no repair/debug framing.

### Metadata
- Task name: landlock-seccomp-notify-admission-mesh
- Title: Landlock Seccomp Admission Mesh
- Category: security
- Languages: [Go, C]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: [tool_specific]
- Tags: [admission, quarantine, landlock, seccomp-notify, path-identity, trust-authority]
- Milestones: 0

### Discovery budget
- Discovery: Path identity for Landlock allow checks must resolve aliases through the durable root map, not the live post-refresh map that decoys bind-mounts into the vault.
  Planned location: environment/qx/internal/fold_a.go plus data/roots/{durable,live}.map
  Why instruction must not reveal it: Naming durable-vs-live map precedence collapses path_drift/symlink diagnosis to a one-line config tip.

- Discovery: Seccomp-notify allow must match the Landlock durable verdict; exec with wire hold must deny, while exec without hold must allow when Landlock allows (broken polarity inverts hold vs pass).
  Planned location: environment/rz/sieve_b.c invoked by nhelper
  Why instruction must not reveal it: Stating the match/exec-hold rule turns notify_skew into a checklist polarity flip.

- Discovery: Ledger emit must quarantine on fd_epoch behind runtime epoch and on revoke-window marks, binding reload_epoch from durable runtime without bumping epoch across mesh-refresh.
  Planned location: environment/qx/internal/emit_c.go plus revoke/window and state/runtime.json
  Why instruction must not reveal it: Publishing FD/revoke ordering and epoch binding makes emit_c a transcription task.

### Anti-trivialization verdict
All 21 checks PASS (see evidence JSON). Residual hardness is authority coupling under sealed EXPECTED, not security aura or harness complexity.

### Topology enumeration (3 candidate fix topologies)
1. **Durable-identity-first** — fold_a.go + sieve_b.c + emit_c.go. Single location insufficient: correct fold alone still fails notify_skew and fd_stale/epoch_revoke.
2. **Notify-match-first** — sieve_b.c + fold_a.go + durable.map. Matching a wrong Landlock input greens notify while path_drift cases still mis-admit.
3. **Emit-authority-first** — emit_c.go + fold_a.go + sieve_b.c. Emit labels reasons only from upstream verdicts; wrong fold/sieve inputs produce wrong quarantine classes.

### Rubric axes
- Verifiable: PASS — deterministic pytest on ledger outcomes.
- Well-specified: PASS — schema tokens and reason vocabulary named.
- Solvable: PASS — expert recoverable in hours.
- Difficult: PASS — three-authority mesh with false-green probe.
- Interesting: PASS — real admission cutover work.
- Outcome-verified: PASS — grades accept/quarantine, not process.

### Hardness axes
- Discover: PASS — durable map, notify polarity, FD/revoke emit.
- Synthesize: PASS — Go×C×maps×revoke×reload.
- Diagnose: PASS — symptoms-only surface vs host.
- Navigate coupling: PASS — partial patches reopen distant classes.
- Reason beyond training: PASS — Landlock×seccomp-notify mesh ≠ Falco/ambient-cap recipes.

### Instruction completeness test
Can the agent solve this by reading ONLY instruction.md without deeply engaging with the codebase? No — precedence, polarity, and emit ordering are codebase/runtime discoveries.

## Reviewer Appendix

### Implementation plan
Ship a Go policy broker and C notify helper that simulate Landlock FS allow checks and seccomp-user-notify open/exec decisions over a scenario matrix. Baseline bodies use live-map identity, inverted exec-hold polarity, and emit that ignores FD/revoke or binds live epoch. Surfcheck uses skim helpers and reports OK on lexical presence. Oracle rewrites fold_a, sieve_b, emit_c, rebuilds, runs admit. Tests embed EXPECTED and re-invoke run-admit after mesh-refresh.

### Proposed file inventory
Matches Authoring Brief Initial Draft Commitments (40+ paths; ≥20 non-Docker under environment/).

### Oracle notes
solve.sh cats correct fold_a.go, sieve_b.c, emit_c.go bodies; `make`; `/app/scripts/run-admit.sh`. Correct fold reads durable.map + allow.list. Correct sieve denies when landlock bit 0 or exec+hold. Correct emit orders fd_stale → epoch_revoke → path_drift → notify_skew → ok_admit; sets reload_epoch from runtime without mutation.

### Collapse audit
Stage: implementation-plan

Smallest plausible successful patch:
Rewrite three decision bodies (~80+ LOC total), rebuild, run admit — not a flag flip.

Likely editable frontier:
- qx/internal/fold_a.go
- rz/sieve_b.c
- qx/internal/emit_c.go

Requirement-to-file map:
- path identity / symlink-bind → fold_a
- notify match / exec hold → sieve_b
- FD / revoke / reload_epoch → emit_c

Oracle estimated complexity: 90–140 non-boilerplate LOC

Red flags:
- none if instruction avoids make-as-task and answer-shaped scenarios

Residual hardness:
After tree is visible, solver still must discover durable-vs-live, hold polarity, and emit ordering under skim bait.

Collapse verdict: PASS

### Naming-pass record

**Instruction nouns extracted:**
job, broker, filesystem, access, rules, syscall, notify, open, exec, mesh, refresh, jobs, surface, probe, host, quarantine, ledger, path, identity, descriptor, inheritance, allow, deny, reload, epochs, scenarios, decision, accept, reason_code, reload_epoch, epoch, runtime, path_drift, fd_stale, notify_skew, epoch_revoke, ok_admit, admission, authority, landlock, seccomp

**Renames during drafting:**
- [`resolve_path_identity` → `fold_a`: avoid path/identity]
- [`notify_decide` → `sieve_b`: avoid notify]
- [`write_quarantine_ledger` → `emit_c`: avoid quarantine/ledger]

**Test names audited:**
- test_m8_obsidian
- test_k3_garnet
- test_n4_topaz
- test_p7_onyx
- test_q7_amber
- test_r1_zircon
- test_t6_jade

**Concentration math:**
- Total tests across flipping_point_contract: 7
- Per location:
  - L1 (qx/internal/fold_a.go): 2/7 = 0.2857
  - L2 (rz/sieve_b.c): 2/7 = 0.2857
  - L3 (qx/internal/emit_c.go): 3/7 = 0.4286
- Cap: 0.5. Max ratio observed: 0.4286. Status: PASS

### Per-test feasibility pre-check
- Test: test_m8_obsidian — Checks: w2 accept/ok_admit — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: LOW
- Test: test_k3_garnet — Checks: k9 quarantine/path_drift — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: LOW
- Test: test_n4_topaz — Checks: n4 quarantine/fd_stale — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: LOW
- Test: test_p7_onyx — Checks: p7 quarantine/notify_skew — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: LOW
- Test: test_q7_amber — Checks: q3 quarantine/epoch_revoke — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: LOW
- Test: test_r1_zircon — Checks: reload stability + schema — Valid approaches: 2+ — Chain-dependent: no (re-runs admit) — Feasibility risk: MEDIUM
- Test: test_t6_jade — Checks: t1 ok_admit + surfcheck≠authority on k9 — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: LOW
