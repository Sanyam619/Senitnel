#include "vcycle.h"
#include "level.h"
#include "grid.h"
#include "stencil.h"
#include "scenario.h"
#include <stdlib.h>

/* Point-wise weighted Jacobi. The classical 2/3 weight damps the
 * highest-frequency eigenmodes of the 5-point Laplacian; the same
 * weight is applied on every level and every scenario. */
void weighted_jacobi_smooth(level_t *lvl, int n_sweeps) {
    int nx = lvl->dims.nx;
    int ny = lvl->dims.ny;
    double omega = lvl->omega;
    double *work = grid_alloc(nx, ny);
    if (!work) return;

    for (int s = 0; s < n_sweeps; s++) {
        stencil_apply(lvl, lvl->u, work);
        for (int i = 1; i < nx - 1; i++) {
            for (int j = 1; j < ny - 1; j++) {
                int k = grid_index(i, j, ny);
                double diag = lvl->A[STENCIL_WIDTH * k + ST_C];
                if (diag == 0.0) continue;
                double r = lvl->f[k] - work[k];
                lvl->u[k] += omega * (r / diag);
            }
        }
    }
    grid_free(work);
}

double relax_weight_for(int level_idx, const scenario_t *scen) {
    (void)level_idx;
    (void)scen;
    return 2.0 / 3.0;
}
