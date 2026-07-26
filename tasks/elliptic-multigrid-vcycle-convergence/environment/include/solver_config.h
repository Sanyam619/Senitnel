#ifndef SOLVER_CONFIG_H
#define SOLVER_CONFIG_H

/* Overall solver identifier written into the JSON summary. */
#define SOLVER_TAG "elliptic-mg-v1"

/* Residual convergence target: relative L2 residual ||r||/||b|| at or
 * below this threshold marks a scenario as converged. */
#define RESIDUAL_TARGET 1.0e-8

/* Hard iteration cap used by the outer V-cycle driver. Scenario budgets
 * live in /app/data/policy/budgets.table and are always smaller than
 * this cap. */
#define MAX_OUTER_ITERATIONS 100

/* Number of grid levels in the hierarchy. */
#define NUM_LEVELS 3

/* Weighted-Jacobi pre- and post-smoothing sweep counts on each level. */
#define N_PRE_SMOOTH 2
#define N_POST_SMOOTH 2

#endif /* SOLVER_CONFIG_H */
