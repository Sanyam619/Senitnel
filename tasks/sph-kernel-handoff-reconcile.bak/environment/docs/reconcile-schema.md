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
| `moment_zero_residual`     | peak relative mismatch between published density and the estimator's partition of unity |
| `h_consistency_residual`   | peak relative mismatch of the mass–smoothing-length constraint after the pass       |
| `momentum_residual`        | relative pairwise force imbalance after the pressure kick                           |
| `angular_residual`         | relative pairwise torque imbalance after the pressure kick                          |
| `gravity_virial_residual`  | relative self-gravity potential mismatch for gravitating scenarios; else 0          |
| `chunk_stability_delta`    | relative range of the per-particle reduction stream across the runner's chunk probes|

The runner owns residual definitions; the numbers must land inside the
per-scenario bands below. Aggregate `invariants` entries are the maxima
of the matching per-row residuals.

## Per-scenario bands

The `band_*` entries in each `data/checkpoints/*.spec` file are the
maximum acceptable residual for that scenario:

| scenario           | moment_zero | h_consistency | momentum | angular | virial | chunk_stability |
|--------------------|------------:|--------------:|---------:|--------:|-------:|----------------:|
| sod_shock_tube     |     1e-4    |    1e-2       |   1e-6   |  1e-6   |   -    |     1e-10       |
| sedov_blast        |     1e-4    |    1e-2       |   1e-6   |  1e-6   |   -    |     1e-10       |
| kelvin_helmholtz   |     1e-4    |    1e-2       |   1e-6   |  1e-6   |   -    |     1e-10       |
| poly_star          |     1e-4    |    1e-2       |   1e-6   |  1e-6   |  5e-2  |     1e-10       |

`sod_shock_tube` is a 1D scenario, so `angular_residual` is
identically zero regardless of implementation; the band is present
only for schema consistency.

## Density estimator (moment-zero) convention

`moment_zero_residual` is the peak relative mismatch between the
published density `rho[i]` and the volume-weighted Shepard-normalized
SPH density estimator. The reference the verifier compares against is

    rho_hat[i] = Σ_j m_j · W(|r_i − r_j|, h_i)
    rho[i]     = rho_hat[i] / [ Σ_j (m_j / rho_hat[j]) · W(|r_i − r_j|, h_i) ]

i.e. the denominator is a Shepard sum with per-particle volume
`m_j / rho_hat[j]`, not a bare kernel sum `Σ_j W_ij`. This is the
sense in which the density field partitions unity: with `rho` defined
this way, `Σ_j (m_j / rho[j]) · W_ij → 1` on a well-resolved
neighborhood. `estimate_density_field` in `sph_a/src/estimator.rs`
must return the tuple `(rho, defect)` with `rho[i]` equal to that
Shepard-normalized value; the verifier probes it directly at ~1e-10
relative tolerance.

## Smoothing-length refinement convention

The smoothing-length pass must iterate rather than declare
convergence after a single step. `refine` in `sph_d/src/iterate.rs`
must honor its `max_steps` argument (do not clamp the budget to `1`)
and perform at least two update steps on any probe field far from
h-consistency before returning `converged = true`; the verifier
rejects a `StepReport` with `steps_run < 2`.

## Configuration authority

When `data/checkpoints/*.spec` reports one `source_kernel` and
`data/policy/handoff.spec` reports a different `selected_kernel`, the
policy value is the source of truth for every downstream computation.
`kernel_target` in the report must be the policy value; `kernel_source`
is informational and reflects the checkpoint entry.

## Chunk-stability

`chunk_stability_delta` is the relative range of the same per-particle
reduction stream evaluated at a set of chunk sizes. The runner probes
{1, 8, 32, N} and reports the resulting delta into the JSON row. The
verifier also exercises the reducer with additional private chunk sizes;
the reduced value must not depend on the chunk size chosen.
