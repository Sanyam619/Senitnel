
### Decision
GO — Attempt 1.

### Metadata
- Task name: systemd-unit-cascade-rollback
- Title: Stack Cutover Rollback
- Category: system-administration
- Languages: ["bash", "rust"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["host", "ops", "rust", "bash", "migration", "recovery"]
- Milestones: 0

### Discovery budget
- Discovery: override merge uses reverse sort so legacy fragment wins BindsTo
  Planned location: environment/scripts/merge-overrides.sh
  Why instruction must not reveal it: would collapse to editing one sort flag
- Discovery: alias table still maps store.service to retired store-v1.service
  Planned location: environment/stack-core/src/merge/op_alias.rs
  Why instruction must not reveal it: names exact stale target
- Discovery: fold_after only retains first After edge breaking topo validation
  Planned location: environment/stack-core/src/graph/op_fold.rs
  Why instruction must not reveal it: pinpoints graph helper

### Anti-trivialization verdict
Passes hidden-instance (all six names listed), multi-location coupling, symptoms-only instruction, verifiable JSON + runtime cross-checks.

### Topology enumeration (3 candidate fix topologies)
1. Graph fold + stackarm ordering + ledger reread — requires op_fold.rs, op_activate.rs, ledgersnap driver
2. Override merge + alias resolution + activation — requires merge-overrides.sh, op_alias.rs, stack-up.sh
3. Full rebuild pipeline with Bash sequencing then depwalk gate — requires all three binary rebuilds plus wrapper scripts

### Rubric axes
All Pass — real ops value, deterministic tests, expert-solvable, hard coupling, outcome graded.

### Hardness axes
Discover/Synthesize/Diagnose/Navigate/Reason-beyond-training satisfied via coupled merge+alias+graph failures with observable tool stderr.

### Instruction completeness test
FAIL if only instruction read — must inspect merge script, Rust sources, and runtime layout.

## Reviewer Appendix

### Implementation plan
Simulated stack lab mirroring cgroup-cutover shape: Bash applies overrides, Rust computes order and activation, ledger reads runtime. Bugs distributed across merge sort, alias map, and truncated After fold.

### Proposed file inventory
20+ files under environment/ per generator output.

### Oracle notes
Patch op_fold for transitive After, fix merge sort ascending, remove store-v1 alias, rebuild, stack-up, depwalk, ledgersnap.

### Collapse audit
Stage: implementation-plan
Smallest plausible patch: three small edits + rebuild — still requires cross-file reasoning.
Collapse verdict: PASS

### Naming-pass record
Instruction nouns extracted: partial, stack, cutover, dependency, ordering, rewired, target, disk, start, attempts, dependent, services, stall, fail, depwalk, after, edges, pairs, ledger, rollback, report, graph, reconciled, config, operator, notes, path, fragments, binaries, rebuild, sources, fixtures, seed, output, version, units, listing, names, state, order, hard, deps, soft, active, override, merge, precedence, resolved, acyclic, valid, sequence, fields, files

Test names audited: test_x3_active_bundle, test_f7_order_chain, test_j2_hard_requires, test_n5_soft_wants, test_p1_shape_bundle, test_r4_anchor_intact, test_h8_tally_matches_runtime, test_k2_relay_bind_resolved

Concentration math: 8 tests; A 2/8=0.25; B 2/8=0.25; C 3/8=0.375; cap 0.5 PASS

### Per-test feasibility pre-check
All LOW risk — deterministic filesystem + JSON assertions.
