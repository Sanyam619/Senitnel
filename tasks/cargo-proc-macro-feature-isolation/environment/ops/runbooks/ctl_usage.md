# Probe usage

`abi_probe` walks `/app/ops/matrix.toml`, builds each cell's crate surface,
stages libraries under `/app/pkg`, compiles the matching C host, and writes
`/output/abi-matrix.json`.

## Cells

- `alpha` / `beta` exercise the macro surface under alternate feature sets.
- `gamma` is a release-profile cdylib cell that resolves libraries through
  pkg-config metadata under `/app/pkg`.
- `delta` exercises the cdylib with an additional lane enabled.
- `epsilon` loads both surfaces in one process and records `tag_families`.

## Report

Each cell reports `status`, `features`, `profile`, `artifact_kind`, and
`version_tags`. Dual-load adds `tag_families` mapping artifact ids to tag
lists. Successful cells report `status` equal to `ok`.
