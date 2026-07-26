# Reconcile Report Schema

The runner emits `/output/reconcile-report.json` shaped as:

```
{
  "schema_tag": "sph-reconcile-v1",
  "scenarios": [ { ...row... }, ... ],
  "invariants": {
    "max_moment_zero":    <f64>,
    "max_momentum":       <f64>,
    "max_angular":        <f64>,
    "max_h_consistency":  <f64>
  }
}
```

Each `scenarios` row has:

| key                        | meaning                                                                             |
|----------------------------|-------------------------------------------------------------------------------------|
| `scenario`                 | scenario name (matches checkpoint spec)                                             |
| `kernel_source`            | kernel that produced the checkpoint                                                 |
| `kernel_target`            | kernel the run is being resumed under                                               |
| `particles`                | particle count for the scenario                                                     |
| `converged`                | JSON boolean; `true` iff the smoothing-length pass reached tolerance                |
| `moment_zero_residual`     | peak relative mismatch between the published density and the raw SPH sum (nonzero on irregular samples is expected) |
| `h_consistency_residual`   | peak relative mismatch of the mass–smoothing-length constraint after the pass       |
| `momentum_residual`        | relative pairwise force imbalance after the pressure kick                           |
| `angular_residual`         | relative pairwise torque imbalance after the pressure kick                          |
| `gravity_virial_residual`  | relative self-gravity potential mismatch for gravitating scenarios; else 0          |
| `chunk_stability_delta`    | relative range of the per-particle reduction stream across the runner's chunk probes|

The runner owns residual definitions; the numbers must land inside the
per-scenario bands below. Aggregate `invariants` entries are the maxima
of the matching per-row residuals.

## Residual liveness

Upper bands are ceilings, not a license to zero every residual by
construction. Across the four scenarios:

- the sum of `h_consistency_residual` must be strictly positive: values
  are the measured post-pass mass–smoothing-length mismatches on
  irregular samples after a genuine multi-step refine, not blanket
  exact zeros from forcing the constraint algebraically and discarding
  the measured residual
- at least one scenario must have `moment_zero_residual > 1e-6`. Values
  near machine epsilon mean the published density collapsed to the raw
  SPH sum (not a live Shepard shift on these irregular layouts)

Correct Shepard normalization still leaves a measurable
`moment_zero_residual` on irregular samples; identity with raw
`rho_hat` fails both this liveness floor and the independent density
probe.

## Density estimator

The density surface used by the runner (and probed by the verifier)
must publish a **partition-of-unity / Shepard-normalized** field, not the
raw SPH kernel sum. With raw SPH density

`rho_hat[i] = Σ_j m_j W(r_ij, h_i)`,

the published density is

`rho[i] = rho_hat[i] / Σ_j (m_j / rho_hat[j]) W(r_ij, h_i)`

(with a small positive floor on denominators). The partition sum uses each
**neighbor** volume `m_j / rho_hat[j]`. Using the center particle's density
for every neighbor volume (`m_j / rho_hat[i]`) is not Shepard normalization
and fails the verifier's independent reconstruction, even after any
handoff scale is removed. Any extra handoff scaling of the published
density that is not part of that normalization also fails the probe.
Pairwise pressure kicks must consume that same published Shepard field —
a private raw SPH sum in the force path fails momentum/angular probes
even when the density surface itself is correct.

## Per-scenario bands

The `band_*` entries in each `data/checkpoints/*.spec` file are the
maximum acceptable residual for that scenario:

| scenario           | moment_zero | h_consistency | momentum | angular | virial | chunk_stability |
|--------------------|------------:|--------------:|---------:|--------:|-------:|----------------:|
| sod_shock_tube     |     0.6     |    1e-2       |   1e-6   |  1e-6   |   -    |     1e-12       |
| sedov_blast        |     0.6     |    1e-2       |   1e-6   |  1e-6   |   -    |     1e-12       |
| kelvin_helmholtz   |     0.6     |    1e-2       |   1e-6   |  1e-6   |   -    |     1e-12       |
| poly_star          |     0.6     |    1e-2       |   1e-6   |  1e-6   |  5e-2  |     1e-12       |

`chunk_stability` (report band and verifier reduction probe) uses the same
relative-drift ceiling of `1e-12`, including on streams with large
canceling scratch terms.

## Policy authority

When `authority = policy_over_checkpoint` in `/app/data/policy/handoff.spec`,
that file's `selected_kernel` (restored from the durable
`/app/data/policy/handoff.canon` sheet on each reconcile) is the sole
kernel authority for every scenario. Sidecar overlay files and
fleet-trial rematerialization must not leave `kernel_target` on the
overlay kernel.

Density and pairwise-force materials follow the durable material root,
not a live fleet trial preference sheet. After a successful reconcile,
`/app/data/state/root.accept` is present with `material_root = durable`,
and `/app/data/state/trial_pref.toml` is absent. While a live trial
preference remains (or the accept is missing / not durable), rebuilds
rematerialize surface trial density and force materials over the
workspace sources — naive one-shot edits to those surfaces do not
survive the next build.

## Smoothing-length pass (`StepReport`)

The public refine surface returns a `StepReport` whose fields the
verifier reads directly:

| field           | meaning / expected probe behavior |
|-----------------|-----------------------------------|
| `max_residual`  | peak relative mass–smoothing-length constraint residual after the pass; must be finite |
| `converged`     | `true` iff `max_residual <=` the caller tolerance |
| `steps_run`     | number of refinement iterations actually executed |

On an irregular field whose initial `h` values are deliberately far from
the mass–density constraint (scaled by ~1.9×), a successful pass with
tolerance `1e-6` and a multi-step budget must leave:

- `max_residual <= 1e-6`
- `converged == true`
- `steps_run >= 2`

## Gravity table

The gravity-table builder used on the virial path is the public function
`greens_table_for_run`. It must remain importable under that exact name
for direct probing. Its published `moment_coeff` must match the active
kernel handle's `second_moment_coeff` (machine precision). Re-deriving
the radial moment by quadrature (or any other substitute) fails that
probe even when report virial bands look plausible.

## Chunked reduction

The shared reduction used for report `chunk_stability_delta` is the
public function `reduce_chunks` (with `chunk_stability_delta` as the
probe helper that exercises it). Both must remain importable under those
exact names. Across the runner's probed chunk sizes, including on streams
with large canceling scratch terms, relative drift must stay within the
`1e-12` ceiling above.

## Verifier probes

The verifier regenerates the report from current sources and calls the
density, gravity-table, force, smoothing-length, and reduction surfaces
with independent particle samples. Report bands alone are not enough:
those surfaces must satisfy the outcomes above under probe inputs.
Existing public probe entry points must stay importable under their
current names — in particular `greens_table_for_run` and `reduce_chunks`
(and `chunk_stability_delta`). Renaming or removing them breaks the
workspace rebuild the verifier uses before those probes can run.
