### Decision
GO — Attempt 2. Data-processing redesign with WAL+lattice coupling; opaque tests; GO evidence.

### Metadata
- Task name: edge-lane-lattice-rollup
- Title: Edge Lane Lattice Rollup
- Category: data-processing
- Languages: ["Rust"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["telemetry", "rollup", "wal", "jsonl", "rust", "lattice"]
- Milestones: 0

### Discovery budget
- WAL frame layout and checksum — fold_a.rs / wal bins — must not be in instruction
- Strict tier_c watermark vs surface tier_b — manifests — must not be named as the fix
- Ship co-presence drops solo mqtt epoch — sieve_b / matrix — must not be recipe-stated

### Anti-trivialization verdict
All 21 checks PASS for data-processing redesign.

### Topology enumeration
See evidence JSON T1–T3.

### Rubric axes
All PASS.

### Hardness axes
All PASS.

### Instruction completeness test
Cannot solve from instruction alone.

## Reviewer Appendix

### Implementation plan
Agent produces derived roster by implementing WAL decode, lattice sieve, and emit against dumps. Surface skim is false-green.

### Proposed file inventory
See authoring spec Initial Draft Commitments (+ seg_003.bin).

### Oracle notes
solve.sh rewrites fold_a, sieve_b, emit_c in Rust and runs pulsectl rollup.

### Collapse audit
Stage: implementation-plan
Collapse verdict: PASS
Residual hardness: co-presence + WAL + strict watermark.

### Naming-pass record
See evidence naming_pass.

### Per-test feasibility pre-check
All six tests: multiple approaches, LOW/MEDIUM risk, not chain-brittle beyond shared output file.
