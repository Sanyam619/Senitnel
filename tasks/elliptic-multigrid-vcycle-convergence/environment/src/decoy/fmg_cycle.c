/* Alternate cycle driver: full multigrid (FMG) startup cycle. Nested
 * iteration from the coarsest level up. Not wired into the built
 * binary (see src/decoy/README). */

#include "vcycle.h"
#include "level.h"
#include "grid.h"
#include "solver_config.h"

extern void weighted_jacobi_smooth(level_t *lvl, int n_sweeps);

void fmg_startup(hierarchy_t *h) {
    /* Coarsest level: zero the solution guess (the shipped
     * coarse_solve_apply is not called here). */
    level_t *coarsest = &h->levels[h->num_levels - 1];
    grid_zero(coarsest->u, coarsest->dims.nx, coarsest->dims.ny);

    for (int L = h->num_levels - 2; L >= 0; L--) {
        /* Prolongate coarser solution into this level's guess. */
        level_t *lvl = &h->levels[L];
        level_t *child = &h->levels[L + 1];
        grid_zero(lvl->u, lvl->dims.nx, lvl->dims.ny);
        prolongate_bilinear_add(lvl, child, child->u, lvl->u);

        /* Post-smooth. */
        weighted_jacobi_smooth(lvl, N_POST_SMOOTH);
    }
}
