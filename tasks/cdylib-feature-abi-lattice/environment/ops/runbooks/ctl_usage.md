# Probe usage

`abi_probe` walks `/app/ops/matrix.toml`, builds the target crate per cell,
emits metadata via `meta_emit`, compiles the matching C host, and writes
`/output/abi-matrix.json`.

## Nuclide cells

Primary lane (`alpha`) resolves facet_a entry points with version tag `NEXUS_2`.
Alt lane (`beta`) resolves facet_b entry points with tag `NEXUS_1B`.
Release lane (`gamma`) consumes pkg-config metadata under `/app/pkg`.

## Cascade cells

Cascade lane (`delta`) resolves facet_c entry points with tag `CASCADE_1C`.
Dual lane (`epsilon`) loads both nuclide and cascade simultaneously and
checks that symbol namespaces do not collide across the two libraries.

## Notes

Cascade and nuclide share dependency crates (k2, n7) but must export
disjoint symbol namespaces. The `cx_` prefix is reserved for cascade;
`nx_` prefix is reserved for nuclide. Version tag families are likewise
distinct: `NEXUS_*` for nuclide, `CASCADE_*` for cascade.
