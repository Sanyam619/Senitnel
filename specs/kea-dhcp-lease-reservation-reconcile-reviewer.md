### Decision
GO — Attempt 1. Same line as authoring spec.

### Metadata
- Task name: kea-dhcp-lease-reservation-reconcile
- Title: Kea DHCP Seating
- Category: system-administration
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: [kea, dhcp, reservation, lease-memfile, conf-fold, generation-gate]
- Milestones: 0

### Discovery budget
- Discovery: durable prefer `pool_root=durable` selects `/var/lib/kea/pools` over live decoys
  Planned location: prefer.toml + bind_v
  Why instruction must not reveal it: naming the knob collapses pool authority
- Discovery: sealed journal tip gens (not live floors) drive subnet generations
  Planned location: journal.jsonl + axle_n
  Why not reveal: floor sheets become the answer key
- Discovery: later-wins conf.d fold shadows prior hw IP into conflicts
  Planned location: mesh_k + 10-core vs site_standard ee:06
  Why not reveal: shadow polarity is the hard coupling
- Discovery: active memfile rows (not expired) block honor on lease collision
  Planned location: memfile.csv + skim_p
  Why not reveal: expired decoy would otherwise teach wrong filter

### Anti-trivialization verdict
Checks 1–21 pass for seating authority coupling; not a single-config knob or three-stub polarity.

### Topology enumeration (3 candidate fix topologies)
1. Prefer×pool + journal tips + emit — still fails fold/shadow/memfile/cutover.
2. Fold×shadow + memfile + abort receipt — still fails durable prefer pools.
3. Full six-helper cutover chain — required; no single helper suffices.

### Rubric axes
Verifiable Pass; Well-specified Pass; Solvable Pass; Difficult Pass; Interesting Pass; Outcome-verified Pass.

### Hardness axes
Discover/Synthesize/Diagnose/Navigate coupling/Reason beyond training — all Pass via multi-locus seating.

### Instruction completeness test
Cannot solve from instruction alone; must recover prefer/fold/memfile/floor/cutover from live desk + docs.

## Reviewer Appendix

### Implementation plan
Bash seating desk writing `/etc/kea` + `/var/lib/kea`; oracle rewrites six helpers + runs seat twice.

### Oracle notes
solve.sh heredoc-fixes helm_r/axle_n/mesh_k/skim_p/bind_v/emit_m then double-invokes entrypoint.

### Collapse audit
Stage: implementation-plan
Smallest plausible successful patch: all six helpers + cutover receipt + site-standard live drop-in.
Collapse verdict: PASS

### Naming-pass record
Instruction nouns: seating, kea, dhcp, reservation, lease, memfile, conf, generation, cutover, schema_tag, subnets, conflicts, seat_ok, honored, …
Test names: mineral (q3_topaz … t4_pearl) — no instruction nouns as substrings.
Concentration: max F 5/14 ≈ 0.36 < 0.5 PASS.
