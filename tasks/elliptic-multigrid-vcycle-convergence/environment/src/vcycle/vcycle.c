#include "vcycle.h"
#include "grid.h"
#include "level.h"
#include "solver_config.h"
#include "scenario.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>

static void vcycle_recurse(hierarchy_t *h, int L) {
    level_t *lvl = &h->levels[L];
    if (L == h->num_levels - 1) {
        coarse_solve_apply(lvl, lvl->f, lvl->u);
        return;
    }
    weighted_jacobi_smooth(lvl, N_PRE_SMOOTH);

    /* Compute residual r = f - A*u on this level, restrict into next
     * level's f, zero next level's u, recurse. */
    residual_compute(lvl, lvl->u, lvl->f, lvl->r);
    level_t *child = &h->levels[L + 1];
    restrict_full_weight(lvl, child, lvl->r, child->f);
    grid_zero(child->u, child->dims.nx, child->dims.ny);

    vcycle_recurse(h, L + 1);

    /* Correction: u += P * child->u. */
    prolongate_bilinear_add(lvl, child, child->u, lvl->u);

    weighted_jacobi_smooth(lvl, N_POST_SMOOTH);
}

int vcycle_solve(hierarchy_t *h, const scenario_t *scen,
                 double *residual_history, double *final_residual) {
    (void)scen;
    level_t *finest = &h->levels[0];
    int nx = finest->dims.nx;
    int ny = finest->dims.ny;

    /* Compute ||b|| on the finest level. */
    double b_norm = grid_l2(finest->f, nx, ny);
    if (b_norm == 0.0) b_norm = 1.0;

    /* Initial u := 0. */
    grid_zero(finest->u, nx, ny);

    double *r0 = grid_alloc(nx, ny);
    residual_compute(finest, finest->u, finest->f, r0);
    double res = grid_l2(r0, nx, ny) / b_norm;
    grid_free(r0);
    if (residual_history) residual_history[0] = res;

    int iter = 0;
    while (iter < MAX_OUTER_ITERATIONS && res > RESIDUAL_TARGET) {
        vcycle_recurse(h, 0);
        double *rk = grid_alloc(nx, ny);
        residual_compute(finest, finest->u, finest->f, rk);
        res = grid_l2(rk, nx, ny) / b_norm;
        grid_free(rk);
        iter++;
        if (residual_history) residual_history[iter] = res;
        if (!isfinite(res)) break;
    }
    if (final_residual) *final_residual = res;
    return iter;
}
