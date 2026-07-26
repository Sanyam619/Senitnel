# partition-invariant-reduction-reconstruction

## Authoring Brief

**Category:** scientific-computing  
**Language:** Rust  
**Difficulty:** hard  

An in-process simulated MPI-style cascade runner performs global scalar reductions over partitioned checkpoint vectors. Floating-point non-associativity plus rank-dependent tree fold order causes checkpoint scalars to drift across 1/2/4/8 rank layouts; overlap cells are double-counted at interior boundaries. The agent must restore bit-exact, layout-invariant scalars against `/app/data/baseline/` and emit ownership maps.

**Symptoms-only instruction.** Agent discovers tree fold in `cascade-mpi/src/stage.rs`, double overlap gather in `cascade-field/src/edge.rs`, and session wiring in `cascade-mpi/src/session.rs`.

### symbol_table

| Symbol | Location |
|--------|----------|
| `gather_lane` | `cascade-field/src/edge.rs` |
| `merge_lane` | `cascade-mpi/src/stage.rs` |
| `fold_vec` | `cascade-mpi/src/stage.rs` |
| `run_session` | `cascade-mpi/src/session.rs` |

### flipping_point_contract

| Location | controls_tests |
|----------|----------------|
| `edge.rs::gather_lane` | overlap_ownership_map, overlap_stress_not_double_counted |
| `session.rs::run_session` | scalars_match_baseline_bitwise, cross_layout_invariance |
| `stage.rs::fold_vec` | cross_layout_invariance (rank-count sensitivity) |

### construction_manifest.code_forbidden_tokens

checkpoint, scalar, rank, layout, overlap, halo, golden, invariant, reduction, partition, reconstruction, dot, product, bit-exact, ownership, double-count

## Reviewer Appendix

Triviality ledger: PASS — fixes require coordinated numerical + ownership reasoning.  
Oracle uses Kahan summation in global index order with deduplicated overlap cells.
