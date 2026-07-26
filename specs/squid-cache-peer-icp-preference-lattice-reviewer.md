### Decision
GO — Attempt 1. Same as authoring spec.

### Metadata
- Task name: squid-cache-peer-icp-preference-lattice
- Title: Squid ICP Peer Seating
- Category: system-administration
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["squid", "cache-peer", "icp", "acl-fold", "peer-journal", "generation-gate"]
- Milestones: 0

### Discovery budget
- Discovery: Sealed+complete prefer batch at gen.target supplies type/weight; incomplete later gen is bait
  Planned location: /var/lib/squid/ops/prefer.jsonl + axle_n
  Why instruction must not reveal it: naming sealed/complete selection collapses tip resolve
- Discovery: Peer journal admit∩¬revoke for sealed gen only; south revoked
  Planned location: peers.jsonl + skim_p
  Why instruction must not reveal it: listing revoked names is answer key
- Discovery: Abort set is union of abort= lines; cutover receipt gates rematerialize
  Planned location: conf.d fold + helm_r + cutover.ok
  Why instruction must not reveal it: recipe for receipt format belongs in docs outcomes only
- Discovery: east floor 8 rejects gen 7; live floors are decoys
  Planned location: durable floors vs /etc/squid/floors
  Why instruction must not reveal it: naming east collapses floor polarity

### Anti-trivialization verdict
Checks 1–21 addressed via coupled prefer×journal×ACL×floor×receipt seating; not policy-knob transcription; not three polarity stubs alone; discovery budget ≥3; topologies ≥3.

### Topology enumeration (3 candidate fix topologies)
1. Receipt-first: helm_r + axle_n + emit_m (≥3); tip alone insufficient without receipt-gated abort skip
2. Journal-first: skim_p + sock_v + emit_m; without journal revoke south greens selected
3. ACL-first: mesh_k + sock_v + emit_m; without abort union core selected

### Rubric axes
Verifiable Pass; Well-specified Pass; Solvable Pass; Difficult Pass; Interesting Pass; Outcome-verified Pass.

### Instruction completeness
Symptoms-only; contract in /app/docs/; schema vocabulary in instruction; entrypoint named.
