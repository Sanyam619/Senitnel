# Evaluation desk notes

Operational notes for the retrieval evaluation rotation. These describe how the
desk behaves; they are not a repair guide.

## Binding

Every run binds to exactly one tip from the feature registry, and everything
downstream of the binding (the effective scale row, the pinned generation in
the report, the composed collections) follows that one choice.

Durable tips are the only tips the published health bands were measured
against. Tips listed in the retired tip ledger are not eligible even when they
are the newest durable row. Live sweep tips move during a recalibration pass
and are never the bound tip for a publishable report.

Evaluation selection and tip bind state live under `calib/`. While selection
stays on the trial setting, or the tip bind receipt does not match the
registry-resolved tip, a refreshed build restores seating surfaces from the
desk seed set. Hand corrections to those surfaces do not survive a rebuild
until selection and tip binding are publishable together.

## Surface sweep artifacts

The file under `data/fixtures/` is a display artifact written by the last
surface sweep. It reflects what the sweep dashboard showed at the time, not
what the desk computes today. It is not an authority and is never read back
by the desk.

The leftover ledger under `data/ledger/` is from an earlier sweep format and
is not the feature-registry tip journal.

## Publishing

The official report is produced by the entrypoint under `scripts/`, which
rebuilds the workspace before emitting. Two consecutive publishes from an
unchanged tree are expected to be byte-identical.
