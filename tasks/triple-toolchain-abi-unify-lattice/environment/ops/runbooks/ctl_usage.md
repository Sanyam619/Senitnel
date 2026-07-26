# Build-matrix utilities

`slotctl` resolves build profiles, applies feature-wire enable bits, and emits
archive packing flags for matrix cells. `hdrgen` materializes the generated
ABI header for a matrix target. `unify_probe` compiles and links every matrix
cell, then writes `/output/unify-report.json`.

Profile pack widths live under `/app/config/profiles`. Facet/width build-stamp
samples live under `/app/data/fixtures/`. Alias drop-ins sit under
`/app/config/lane.d/`. Packing preference, cutover, fold, hook, and release
mask notes live under `/app/ops/nx/`. Cutover journal samples live under
`/app/data/fixtures/desk_journal.jsonl`. Archive archaeology and graph seeds
remain under `/app/link/`.

The status script only checks that build utilities are installed; it does not
validate profile propagation, packing policy, or matrix artifacts.
