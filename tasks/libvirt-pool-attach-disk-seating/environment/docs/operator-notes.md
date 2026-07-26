# Operator notes

The reconcile engine (`/app/bin/virtattach`, invoked by the entrypoint) is
sealed. It consumes the state that the ops helpers stage and writes the seating
report. It does not resolve identities on its own — it applies what the staging
steps produce and rewrites each domain disk binding to the selected identity on
every run.

## Selection drop-ins

`attach.d` drop-ins carry an `authority` key. Supported values:

- `authority=durable` — bind each disk to the identity recorded in the cutover
  journal (resolved up to the sealed generation).
- `authority=surface` — bind each disk to the pool definition file exactly as it
  is currently written.

The highest-numbered drop-in wins. When nothing selects a value the engine falls
back to the surface definition.

## Staging steps

The entrypoint runs a handful of small staging helpers (under `/app/ops/` and
`/app/stage/`) before the engine:

- a resolver that writes the per-pool seating plan the engine consumes,
- a pool activator that seeds runtime state,
- a receipt writer that records the cutover authorizations,
- a lease janitor that clears crash-era markers under `/var/run/libvirt/`.

Receipts are plain `key=value` records (`pool=`, `uuid=`, `volume=`). A disk is
only seated when its pool is active, its binding matches the journal identity,
and a matching receipt is present.

## Health

`virthealth` reports on definition-file presence only. A healthy line there does
not mean any disk is actually seated.
