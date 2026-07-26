# wasm tier-up admission lab

C host that reconciles profile, rebind, and floor authorities for a
tenant guest matrix after a registry restore incident.

## Build

Rebuild `/app/bin/warmup` from the sources under `src/` (for example via
`make`). Drivers: `scripts/run-engine.sh`, `scripts/show-coredump.sh`.
Soft probe: `scripts/fastcheck` (not the admit authority). Policy:
`docs/authority-notes.md`.
