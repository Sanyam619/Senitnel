# Campaign report schema (nbody-campaign-v1)

Output path: `/output/campaign-report.json`

Top-level fields:
- `schema_tag` (string): must be exactly `nbody-campaign-v1`
- `cases` (array of objects)
- `parity` (object)

Each element of `cases`:
- `label` (string): case directory name (`plummer`, `binary`, or `collapse`)
- `workers` (int): 1, 2, or 4
- `mode` (string): `cold` or `resume`
- `energy` (number): total mechanical energy (kinetic + softened potential) over interior bodies
- `momentum_L2` (number): L2 norm of total linear momentum over interior bodies
- `mass` (number): sum of mass over interior bodies
- `stable` (bool): true iff all reported math fields are finite and mass is positive

`parity` object:
- `cold_resume_max_rel` (number): max relative gap between cold and resume rows that share label+workers, taken over energy, momentum_L2, mass
- `worker_spread_max_rel` (number): max relative spread across workers for cold rows of the same label, taken over the same fields

Relative gap for a pair (a,b): `|a-b| / max(|a|, |b|, 1e-12)`.
Relative spread for a set: `(max-min) / max(|max|, |min|, 1e-12)`.

Agreement bands used by the campaign driver when filling parity (also enforced by the verifier):
- cold/resume max relative gap must be ≤ `1e-4`
- worker spread max relative must be ≤ `1e-3`
- mass closure: `|mass - sum(particle masses)| / sum(particle masses) ≤ 1e-2` for every row

Checkpoint / padded-state halo
------------------------------

Mid-run checkpoints serialize a padded worker state and later restore it.
A conforming round trip must satisfy all of the following (the verifier
exercises this path with its own padded inputs, not only through cold/resume
report numbers):

1. Interior bodies restore in live partition **slot order** along the primary
   axis. Reordering interiors by a secondary coordinate before materializing
   the durable payload breaks resume identity even when masses and counts
   look fine.
2. The trailing **halo** appendix must be long enough for both ghost strips
   (west and east). Payload length is interiors plus both strips.
3. After restore, each west ghost slot at depth `k` must hold the body that
   currently sits in the west-adjacent interior at the same depth, and each
   east ghost slot at depth `k` must hold the east-adjacent interior at the
   same depth. Values that already occupy the ghost buffer **before** the
   durable write are not authoritative: after a mid-run interior reorder
   those slots can be stale, so the halo must be re-derived from the current
   interior edges rather than copied from the pre-write ghost region.

A campaign whose cold/resume macroscopic gaps look green can still fail if
checkpoint materialization preserves stale ghosts or ranks bodies on a
secondary axis instead of primary-axis slot order.

Configuration authority
-----------------------

When the run manifests under `config/manifests/` disagree with any
compile-time defaults elsewhere in the campaign source (for example, values
declared under `internal/buildmeta`), the run manifests are authoritative
for every observable that appears in `cases`. The physical bounds recorded
below follow from running each case under the physics declared in its
manifest; a campaign that reports observables consistent with any other
source of the same knob is not conforming, even if the numeric agreement
bands above are satisfied.

Physical bounds enforced by the verifier
----------------------------------------

The `plummer` case is a rotating disk IC (see `data/cases/plummer/particles.json`).
Under the run manifest at `config/manifests/plummer.toml` the 28-step campaign
settles into an attractor whose total mechanical energy magnitude satisfies
`|energy| ≥ 0.55` for every cold worker count. This value is the observable
indicator of the "Configuration authority" rule above: it is the energy the
manifest-governed plummer attractor produces, and no report that reflects a
different physics source will meet it.

The verifier enforces:
- `plummer_energy_floor`: for every `plummer` row with `mode = "cold"`, `|energy| ≥ 0.55`.

Reports that fall below this floor are rejected even if the parity, mass-closure and
worker-spread bands above are all satisfied.
