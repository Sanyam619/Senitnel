#ifndef VCYCLE_H
#define VCYCLE_H

#include "level.h"

/* Apply the 9-point stencil at every interior node of the level and
 * write A * u into `out`. Boundary nodes (Dirichlet u = 0) are treated
 * as prescribed zero. */
void stencil_apply(const level_t *lvl, const double *u, double *out);

/* Compute r = f - A * u on the interior; boundary entries are set to 0. */
void residual_compute(const level_t *lvl, const double *u,
                      const double *f, double *r);

/* Full-weighting restriction from `fine` to `coarse` using the
 * `to_child` axis-transfer descriptor of the fine level. */
void restrict_full_weight(const level_t *fine, const level_t *coarse,
                          const double *fine_field, double *coarse_field);

/* Bilinear prolongation from `coarse` to `fine`; the result is ADDED
 * to `fine_field` (multigrid correction update). */
void prolongate_bilinear_add(const level_t *fine, const level_t *coarse,
                             const double *coarse_field, double *fine_field);

/* Assemble the fine-grid 5-point stencil from the scenario coefficient
 * laws. Writes into `lvl->A`. Boundary rows are cleared. */
void fine_operator_assemble(level_t *lvl, const scenario_t *scen);

/* Build the coarse-grid operator from the fine-grid operator. Produces
 * an operator whose action on coarse-grid vectors approximates the
 * fine operator's action on prolongated vectors, projected back via
 * restriction. */
void coarse_operator_assemble(const level_t *fine, level_t *coarse);

/* Weighted Jacobi smoother: apply `n_sweeps` weighted-Jacobi updates
 * to lvl->u using lvl->f as the right-hand side. Uses lvl->omega. */
void weighted_jacobi_smooth(level_t *lvl, int n_sweeps);

/* Choose the relaxation weight for a given (level, scenario) pair. */
double relax_weight_for(int level_idx, const scenario_t *scen);

/* Coarse-level direct solve (LU with partial pivoting). Populated by
 * coarse_solve_prepare on the coarsest level, executed by
 * coarse_solve_apply. */
int coarse_solve_prepare(level_t *lvl);
void coarse_solve_apply(const level_t *lvl, const double *f, double *u);

/* Run V-cycles on the hierarchy until residual < RESIDUAL_TARGET or
 * MAX_OUTER_ITERATIONS is reached. Returns iteration count. Appends
 * residual history to trace_out if non-NULL. */
int vcycle_solve(hierarchy_t *h, const scenario_t *scen,
                 double *residual_history, double *final_residual);

#endif /* VCYCLE_H */
