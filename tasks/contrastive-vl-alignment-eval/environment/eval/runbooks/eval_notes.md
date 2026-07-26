# Contrastive vision–language evaluation notes

Notes for the held-out image–caption retrieval evaluation rotation. These
describe how the desk behaves; they are not a repair guide.

## Binding

Every run binds to exactly one tip from the tip journal under the feature
registry, and everything downstream of the binding (the logit-scale /
negative-pool schedule pair, the tip generation in the report, the composed
image banks) follows that one choice.

Durable tips are the only tips the published health bands were measured
against. Tips listed in the retired tip ledger are not eligible even when
they are the newest durable row. Live shadow-bank tips move during a
recalibration pass and are never the bound tip for a publishable report.

Evaluation selection and tip bind state live under `calib/`. While selection
stays on the trial setting, or the tip bind receipt does not match the
registry-resolved tip, a refreshed evaluation run restores seating surfaces
from the desk seed set. Hand corrections to those surfaces do not stick until
selection and tip binding are publishable together.

## Surface probe

`/app/tools/vlprobe` scores train-set overlap on the surface fixture only. It
may report aligned while deep contrastive VL evaluation is still unhealthy.
The file under `data/fixtures/` is a display artifact from the last surface
sweep — including an inbatch pool seating — and is never read back by the
desk.

The leftover ledger under `data/ledger/` is from an earlier sweep format and
is not the tip-journal authority.

## Publishing

The official report is produced by the entrypoint under `scripts/`. Two
consecutive publishes from an unchanged tree are expected to be
byte-identical.
