# Enrollment stack layout

The lab enrolls framed update records through three small tools that are wired
together by a shell entrypoint. Each tool owns one concern and hands a compact
JSON view to the next stage.

## Components

- `frame/` builds `framectl` (C). It reads a record from `data/capsules/` and
  emits a one-line JSON view of the leaf, parent tip, generation, and the
  surface checks. It also exposes a `skim` mode used by the advisory surface
  pass.
- `policy/` builds `polgate` (Rust). Given a record id and its claimed
  generation, it consults `data/revoke/current.rl` and `data/revoke/window.toml`
  and returns a numeric policy code.
- `enroll/` builds `enrollctl` (Go). It reads the runtime state, iterates the
  scenarios under `data/scenarios/`, invokes the framing and policy tools, binds
  against the root material under `data/roots/`, and writes the ledger.

## Data

- `data/state/runtime.json` holds the active epoch and lane.
- `data/roots/` holds the root bundles. `disk.bundle` is the durable copy;
  `live.bundle` is the copy the running host currently holds.
- `data/revoke/` holds the current mark list and the freshness bounds.
- `data/scenarios/` holds one file per device/record pairing.
- `data/capsules/` holds the framed record payloads.

## Build and run

`make` builds all three tools into `bin/`. `scripts/run-enroll.sh` runs the
enrollment pass. `scripts/host-reload.sh` promotes the durable bundle into the
live slot. `scripts/rebuild-tools.sh` is a thin wrapper over `make`.
