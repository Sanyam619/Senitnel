# Desk outcome sheet

`/output/sign-ledger.json` and `/output/quarantine.json` use version 1.
Ledger fields: backends, epochs (id, profile, accepted).
Quarantine fields: rejected rows with epoch, lane, ts, reason.

Deep SoftHSM admission must disagree with the surface fixture. Durable token
preference must beat live surface bind so material survives rebuild.

## Backends vocabulary

Matrix lanes report active when they contribute Active frames under a published
epoch. Off-matrix lanes stay inactive.

## Epoch scenarios

- Novel epoch 15 publishes under fleet_a when deep material is restored.
- Epoch 25 does not publish: required lane is only revoked.
- Epoch 30 publishes under hold co-presence; held frames are omitted from the
  ledger accepted count, so accepted stays reduced versus a no-hold reading of
  the same stream.
- Watermark fences include the boundary timestamp.

## Quarantine shape

One rejected row per rejected WAL frame (no dedup across frames). Reasons are
integrity_failure, replay, and revoked only.
