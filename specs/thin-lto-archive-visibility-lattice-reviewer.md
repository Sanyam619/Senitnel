### Decision
GO — Attempt 1. Thin-LTO archive visibility lattice under build-and-dependency-management with four coupled loci (Cargo digest/epoch forward, C visibility forge, Go cgo membership, profile authority). Symptoms-only instruction; observation-only probe; verifier-owned EXPECTED; probe ok requires profile-declared bitcode_epoch (not mutual agreement).

### Metadata
- Task name: thin-lto-archive-visibility-lattice
- Title: Thin-LTO Archive Lattice
- Category: build-and-dependency-management
- Languages: ["C", "Rust", "Go"]
- Difficulty: hard
- Codebase size: small
- Subcategories: ["tool_specific"]
- Tags: ["thin-lto", "staticlib", "cgo", "visibility", "archives", "profiles"]
- Milestones: 0

### Discovery budget
- Discovery: lane_k1 always returns the ship profile path, so fleet cells inherit ship bitcode_epoch=3
  Planned location: g5/auth.go
  Why instruction must not reveal it: Naming the profile path picker collapses to a one-line string rewrite.
- Discovery: knit_v4 drops the strand_a visibility bit on ship-only cells
  Planned location: r7/src/knit.rs
  Why instruction must not reveal it: Naming the digest-bit polarity becomes a single boolean flip recipe.
- Discovery: emit_q3 hardcodes bitcode_epoch 3 whenever strand_b is set
  Planned location: vis/emit_q3.c
  Why instruction must not reveal it: Pointing at the visibility forge removes the header/packing coupling.
- Discovery: cg_n5 expands ship membership under strand_a-only and collapses fleet membership under strand_b
  Planned location: g5/pack.go
  Why instruction must not reveal it: Naming the packing mirror removes the locally-green distant-fail trap.

### Anti-trivialization verdict
All 21 checks PASS. Not disclosure-collapse (symptoms-only). Not hidden-instance (fixed matrix). Not single-artifact. Not orthogonal checklist (four coupled loci). Discovery budget ≥3. Topology distribution ≥3. Hard-only gate PASS.

### Topology enumeration (3 candidate fix topologies)
- T1 Authority-first: lane_k1 → emit_q3 → cg_n5 → knit_v4. Authority alone insufficient (strand_b forge/packing + ship digest remain).
- T2 Visibility/packing-first: emit_q3 → cg_n5 → lane_k1 → knit_v4. Aligned packing still fails when fleet cells read ship and alpha digest bits wrong.
- T3 Digest-first: knit_v4 → lane_k1 → emit_q3 → c9 objects. Alpha-only repair leaves fleet forge/packing/authority failing.

### Rubric axes
- Verifiable: PASS — deterministic probe JSON + EXPECTED
- Well-specified: PASS — clear lattice-report outcomes
- Solvable: PASS — expert hours, bounded oracle
- Difficult: PASS — multi-toolchain profile lattice
- Interesting: PASS — real fleet archive cutover
- Outcome-verified: PASS — grades report, not process

### Instruction completeness
PASS — instruction alone insufficient; must engage codebase for four loci.

### Attack path
Read matrix/profiles → diagnose authority/forward/forge/packing → reconcile → rebuild → lattice_probe.

### Smallest plausible patch
Restore live profile path, strand_a digest forward, profile-honoring epochs, and strand-conditional membership — not one file.

### Collapse audit
PASS — residual hardness is four-way coupling + agreement-on-wrong-epoch trap + surface link-ok bait.
