### Decision
GO — Attempt 1. SoftHSM-class Traefik file-provider seating lattice.

### Metadata
- Task name: traefik-dynamic-router-file-seating
- Title: Traefik Router Seating
- Category: system-administration
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: ["tool_specific"]
- Tags: ["traefik", "dynamic-router", "middleware", "file-provider", "generation-gate", "ops-seating"]
- Milestones: 0

### Discovery budget
- Discovery: Serving tip is newest durable journal tip excluding retired_tips; tip_live and tip_g9 are baits
  Planned location: journal.jsonl + retired_tips.jsonl + axle_n
  Why instruction must not reveal it: Tip ids would become an answer key
- Discovery: knit_q rematerializes surface router seeds unless prefer is durable/authority and tip_bind matches resolved tip
  Planned location: prefer.toml + tip_bind.accept + knit_q.sh
  Why instruction must not reveal it: Two-knob checklist collapse
- Discovery: Middleware attached comes from mw_prefer.toml not live decoy chain; abort must not revoke seated routers after matching cutover.ok
  Planned location: mw_prefer.toml + skim_p + helm_r + mesh_k
  Why instruction must not reveal it: Would map requirements to exact fix files

### Anti-trivialization verdict
All 21 checks PASS.

### Topology enumeration (3 candidate fix topologies)
T1: prefer-gate-rematerialize — ops/prefer.toml, ops/tip_bind.accept, wire/knit_q.sh. Prefer without bind still rematerializes; bind without knit still seats decoys
T2: abort-cutover-fold — ops/helm_r.sh, rim/mesh_k.sh, var/lib/traefik/ops/state/cutover.ok. Receipt without fold still revokes; fold without receipt rematerializes abort
T3: tip-floor-middleware — ops/axle_n.sh, bag/skim_p.sh, deck/emit_m.sh. Tips alone leave mw wrong; mw alone leaves active/floor wrong

### Rubric axes
All six PASS.

### Hardness axes
All five PASS.

### Instruction completeness test
No — instruction alone is insufficient.

## Reviewer Appendix

### Implementation plan
Broken bash seating pipeline with SoftHSM prefer rematerialize; oracle commits durable prefer + tip_bind and rewrites helpers.

### Proposed file inventory
Matches constructed tasks/traefik-dynamic-router-file-seating/environment tree (20+ files).

### Oracle notes
solve.sh overwrites helpers + prefer/bind then runs seating twice.

### Collapse audit
Stage: implementation-plan. Residual hardness: prefer×bind rematerialize + tip retirement + abort-not-revoke + floor active.
