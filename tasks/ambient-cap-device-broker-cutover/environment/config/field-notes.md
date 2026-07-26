# Broker lab field notes

## Surface check

`topsurf` reports unit ActiveState plus node presence under either mount tree.
It does not inspect capability state, drop-in fragments, or namespace placement.

## Diagnostic

`nsprobe` dumps mnt_ns identity, ambient/bounding contents, and PrivateDevices from the primary live unit file.

## Unit fragments

Primary unit: `/data/lab/units/live.service`.
Drop-in directory: `/data/lab/units/live.d/`. Fragments there merge into the effective unit policy for device isolation.

## Configuration profiles

Profile configs live under `/opt/broker/config/`. The active profile is set in `lab.toml` and determines the authoritative capability boundary. Harbor profile is retained for compatibility only.

## Legacy mode

The `--legacy` flag on `laneapply` overwrites capability files with a broader set including `cap_sys_rawio`. That path is not for production cutover. Bounding must come from the active profile.

## Mutators

`ledgerout --fold` rewrites the primary live unit PrivateDevices line.
`ledgerout --emit` reads current disk state and writes the cutover ledger.
Lane propagation consults the effective PrivateDevices policy before copying bounding into ambient and effective.
Race pulse requires broker identity plus seated nodes with no host stale markers.
