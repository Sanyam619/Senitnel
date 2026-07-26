# Campaign report schema (lbm-campaign-v1)

Output path: `/output/campaign-report.json`

Top-level fields:
- `schema_tag` (string): must be exactly `lbm-campaign-v1`
- `cases` (array of objects)
- `parity` (object)

Each element of `cases`:
- `label` (string): case directory name (`poiseuille`, `cavity`, or `couette`)
- `workers` (int): 1, 2, or 4
- `mode` (string): `cold` or `resume`
- `mean_rho` (number): mean density over interior cells
- `mom_x` (number): mean x-momentum over interior cells
- `mom_y` (number): mean y-momentum over interior cells
- `ke` (number): mean kinetic energy over interior cells
- `mass` (number): sum of density over interior cells
- `stable` (bool): true iff all moments are finite

`parity` object:
- `cold_resume_max_rel` (number): max relative gap between cold and resume rows that share label+workers, taken over mean_rho, mom_x, mom_y, ke, mass
- `worker_spread_max_rel` (number): max relative spread across workers for cold rows of the same label, taken over the same fields

Relative gap for a pair (a,b): `|a-b| / max(|a|, |b|, 1e-12)`.
Relative spread for a set: `(max-min) / max(|max|, |min|, 1e-12)`.

Agreement bands used by the campaign driver when filling parity (also enforced by the verifier):
- cold/resume max relative gap must be ≤ `1e-3`
- worker spread max relative must be ≤ `1e-3`
- mass closure: `|mass - nx*ny*rho0| / (nx*ny*rho0) ≤ 1e-2` for every row

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

The `cavity` case is lid-driven at `u_lid = 0.02` (see `data/cases/cavity/grid.json`).
Under the run manifest at `config/manifests/cavity.toml` the 40-step campaign settles
into an attractor whose interior mean x-momentum satisfies `|mom_x| ≥ 7e-3` for every
worker count. This value is the observable indicator of the "Configuration
authority" rule above: it is the mean x-momentum the manifest-governed
cavity attractor produces, and no report that reflects a different physics
source will meet it.

The verifier enforces:
- `cavity_mom_x_floor`: for every `cavity` row with `mode = "cold"`, `|mom_x| ≥ 7e-3`.

Reports that fall below this floor are rejected even if the parity, mass-closure and
worker-spread bands above are all satisfied.
