### Decision
GO — Attempt 1. Hard system-administration HAProxy runtime-drain backend seating with coupled conf.d fold × runtime socket apply × drain leases × durable generation floors × abort rematerialize receipt.

### Metadata
- Task name: haproxy-runtime-drain-seating
- Title: HAProxy Drain Seating
- Category: system-administration
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["haproxy", "backend-seating", "runtime-socket", "drain-window", "generation-gate", "conf-fold"]
- Milestones: 0

### Discovery budget
- Discovery: Drain leases set drained=true while preserving folded weight; weight-zero is not the drain polarity.
  Planned location: `/app/bag/skim_p.sh` + leases under `/var/lib/haproxy/leases/` + docs seating_contract.md
  Why instruction must not reveal it: Naming the polarity collapses the drain vs weight-zero trap into a one-line recipe.

- Discovery: Runtime socket state under `/var/run/haproxy/runtime.map` must match folded weights/drains; file-only conf edits leave socket_applied false.
  Planned location: `/app/wire/sock_v.sh` + `/var/run/haproxy/`
  Why instruction must not reveal it: Agents otherwise green conf.d and skip socket apply.

- Discovery: Durable floors live under `/var/lib/haproxy/floors/`; live `/etc/haproxy/floors/` are decoys. Tip generations come from journal cutover to gen.target.
  Planned location: `/app/ops/axle_n.sh` + durable floors + journal.jsonl
  Why instruction must not reveal it: Would turn generation seating into transcription of which path is authoritative.

- Discovery: Abort package rematerializes into live 90-local unless cutover.ok matches gen.target+mode=seal; live drop-in must stay present with site-standard tokens.
  Planned location: `/app/ops/helm_r.sh` + abort.d + cutover.ok
  Why instruction must not reveal it: Delete-vs-rewrite ambiguity collapses receipt handling (backup-restore class).

### Anti-trivialization verdict
1 Disclosure-collapse: PASS — honest outcomes still need coupled authorities.
2 Hidden-instance: PASS — multi-backend matrix, not one broken file.
3 Single-artifact: PASS — ≥6 coordinated helpers.
4 Generalization: PASS — full roster matrix.
5 Prompt-honesty: PASS — symptoms + fair schema; no named broken helper.
6 Cheating-vs-difficulty: PASS — digest pins are anti-cheat only.
7 Mechanical-fix: PASS — domain seating work.
8 Localized-fix: PASS — distributed loci.
9 Oracle-locality: PASS — oracle rewrites ≥6 helper bodies.
10 Small declarative-cluster: PASS — fold×socket×drain×gen×receipt.
11 Grep-collapse: PASS — opaque symbols.
12 Pre-factored-helper: PASS — mesh_k/axle_n/skim_p not prompt nouns.
13 Recipe-discount: PASS — not textbook HAProxy tutorial alone.
14 Security-aura: PASS — sysadmin seating, not crypto costume.
15 Orthogonal-checklist: PASS — local fix invalidates distant cells.
16 Harness-discount: PASS — single container, simulated socket.
17 One-pass solvability: PASS — surface UP + decoy floors + rematerialize.
18 Hard-only: PASS — designed hard.
19 Discovery budget: PASS — ≥3 discoveries.
20 Instruction specificity: PASS — symptoms-only with fair schema outcomes.
21 Topology distribution: PASS — see below.

### Topology enumeration (3 candidate fix topologies)
1. Ops-helper rewrite: mesh_k + axle_n + skim_p + helm_r + sock_v + emit_m must coordinate; fixing only fold leaves socket/drain/gen red.
2. Durable-authority restore: journal tip apply + floors + cutover receipt + abort forensic; single path insufficient because socket and drain still diverge.
3. Socket-first seating: sock_v + emit_m + fold agreement; still fails without drain lease polarity and generation floors.

### Rubric axes
1 Verifiable — Pass: deterministic pytest on seating JSON + live state.
2 Well-specified — Pass: schema + seating rules in instruction/docs.
3 Solvable — Pass: expert ops hours with docs.
4 Difficult — Pass: coupled authorities, rematerialize, surface bait.
5 Interesting — Pass: real HAProxy drain/seat ops value.
6 Outcome-verified — Pass: grade JSON + live /etc /var, not process.

### Hardness axes
- Discover: durable vs live floors, drain≠zero, socket map, receipt format.
- Synthesize: fold × socket × drain × gen × receipt × emit.
- Diagnose: symptoms (UP health, seat_ok false, abort residual) not causes.
- Navigate coupling: local weight edit rematerialized; socket mismatch after fold-only.
- Reason beyond training: lab-specific journal+receipt+floor coupling.

### Instruction completeness test
No — instruction alone lacks which floors path is durable, how runtime.map is shaped, lease file layout, and which abort synonyms rematerialize. Solver must read docs/helpers/runtime state.

## Reviewer Appendix

### Implementation plan
Ship broken bash helpers that write live HAProxy admin trees. Correct seating requires rewriting fold, generation align, drain lease materialize, abort rematerialize gate, socket apply, and ledger emit. Surface proxyhealth always UP. Verifier re-enters seating and derives EXPECTED from durable fixtures.

### Proposed file inventory
Matches authoring Initial Draft Commitments (≥20 env files excl. Docker).

### Oracle notes
solve.sh rewrites mesh_k, axle_n, skim_p, helm_r, sock_v, emit_m with correct bodies (≥30 LOC), writes matching cutover.ok after helpers prepare state via entrypoint, leaves fixtures pinned.

### Collapse audit
Stage: implementation-plan

Smallest plausible successful patch:
Rewrite six helper scripts so fold, floors, drain, receipt, socket, and emit agree — not a one-file sed.

Likely editable frontier:
- rim/mesh_k.sh, ops/axle_n.sh, bag/skim_p.sh, ops/helm_r.sh, wire/sock_v.sh, deck/emit_m.sh

Requirement-to-file map:
- fold weights -> mesh_k
- generations -> axle_n
- drain -> skim_p
- rematerialize -> helm_r
- socket -> sock_v
- ledger -> emit_m

Oracle estimated complexity: 120+ non-boilerplate lines

Red flags:
- none if opaque names and no answer-key instruction

Residual hardness:
After tree visible, agent still must discover durable floor path, drain≠zero, socket map contract, and receipt format under rematerialize pressure.

Collapse verdict: PASS

### Naming-pass record

**Instruction nouns extracted:**
proxy, seat, backend, backends, drain, drained, weight, generation, socket, fold, conf, lease, haproxy, runtime, schema, applied, receipt, cutover, abort, floor, floors, roster, server, servers

**Renames during drafting:**
- None — first-pass naming was already clean against the forbidden list (opaque mesh_k/axle_n/skim_p/helm_r/sock_v/emit_m)

**Test names audited:**
- test_q3_topaz
- test_n4_beryl
- test_w7_quartz
- test_j2_onyx
- test_v5_coral
- test_p9_jade
- test_h8_amber
- test_c1_flint
- test_r6_slate
- test_u2_mica
- test_m1_opal
- test_t4_pearl

**Concentration math:**
- Total tests across flipping_point_contract: 12
- Per location:
  - L1 (rim/mesh_k.sh): 4/12 = 0.333
  - L2 (ops/axle_n.sh): 3/12 = 0.250
  - L3 (bag/skim_p.sh): 3/12 = 0.250
  - L4 (ops/helm_r.sh): 3/12 = 0.250
  - L5 (wire/sock_v.sh): 3/12 = 0.250
  - L6 (deck/emit_m.sh): 4/12 = 0.333
- Cap: 0.5. Max ratio observed: 0.333. Status: PASS

### Per-test feasibility pre-check
- Test: test_q3_topaz — schema+seat_ok — approaches: 2+ — chain: no — risk: LOW
- Test: test_n4_beryl — idempotence — approaches: 2+ — chain: no — risk: LOW
- Test: test_w7_quartz — digest pin — approaches: 1 — chain: no — risk: LOW
- Test: test_j2_onyx — fold weights — approaches: 2+ — chain: no — risk: LOW
- Test: test_v5_coral — generation polarity — approaches: 2+ — chain: no — risk: MEDIUM
- Test: test_p9_jade — drain≠zero — approaches: 2+ — chain: no — risk: MEDIUM
- Test: test_h8_amber — abort forensic — approaches: 2+ — chain: no — risk: MEDIUM
- Test: test_c1_flint — cutover receipt — approaches: 2+ — chain: no — risk: MEDIUM
- Test: test_r6_slate — socket apply — approaches: 2+ — chain: no — risk: MEDIUM
- Test: test_u2_mica — backends coupling — approaches: 2+ — chain: no — risk: LOW
- Test: test_m1_opal — full matrix — approaches: 2+ — chain: no — risk: MEDIUM
- Test: test_t4_pearl — surface UP — approaches: 2+ — chain: no — risk: LOW
