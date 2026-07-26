# Operator notes for the gateway cutover matrix.

The matrix under `/app/ops/matrix.toml` lists host and supervisor cells
(alpha through epsilon). `status_check.sh` only confirms tree presence.
Use `lattice_probe` for load outcomes in `/output/lattice-report.json`.

Host-role cells expose a `flags` object (CC, PIE, and related stamps). Those
stamps are a stamp-only simulation of the cutover contract. The musl target
host lane is expected to stamp a musl static-PIE toolchain (`musl-gcc`,
`-fPIE` / `-pie`) in that flags object.

Shared headers live under `/app/include/`. Profile knobs are under `/app/config/profiles/`.

Probe sources that must stay intact:
`/app/tools/probe/main.go`, `/app/tools/probe/go.mod`.
