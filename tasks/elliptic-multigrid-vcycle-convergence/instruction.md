A three-level V-cycle elliptic solver under `/app` builds with `make` and
runs via `/app/scripts/run_solve.sh`. It walks `/app/data/scenarios/` and
writes `/app/output/`. Every scenario currently hits the outer iteration
cap without meeting the residual target in `/app/include/solver_config.h`
within the budgets in `/app/data/policy/budgets.table`. Fix the solver so
each scenario finishes under budget with residual at or below that target.

Emit `/app/output/convergence.json` (solver_tag, all_within_budget, and
scenarios entries with label, iterations, residual, budget). Emit residual
traces `/app/output/traces/s_iso.trace`, `/app/output/traces/s_aniso.trace`,
`/app/output/traces/s_jump.trace`, `/app/output/traces/s_corner.trace`,
`/app/output/traces/s_mixed.trace` (one float per V-cycle) and fields
`/app/output/fields/s_iso.f64`, `/app/output/fields/s_aniso.f64`,
`/app/output/fields/s_jump.f64`, `/app/output/fields/s_corner.f64`,
`/app/output/fields/s_mixed.f64` (little-endian float64, i-slow j-fast per
`/app/include/grid.h`). Traces must be non-increasing; when a run takes
more than one V-cycle the average per-V-cycle geometric residual reduction
must be at most 0.4; field boundaries stay Dirichlet zero.

Do not weaken budgets or the residual target, skip scenarios, or fabricate
traces. Scoring rebuilds from `/app` and wipes `/app/output/` first.
