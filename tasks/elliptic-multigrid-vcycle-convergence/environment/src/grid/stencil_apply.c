#include "vcycle.h"
#include "grid.h"
#include "stencil.h"

void stencil_apply(const level_t *lvl, const double *u, double *out) {
    int nx = lvl->dims.nx;
    int ny = lvl->dims.ny;
    /* Zero output including boundary rows / cols. */
    grid_zero(out, nx, ny);
    for (int i = 1; i < nx - 1; i++) {
        for (int j = 1; j < ny - 1; j++) {
            const double *coef = &lvl->A[STENCIL_WIDTH * grid_index(i, j, ny)];
            double s = 0.0;
            for (int k = 0; k < STENCIL_WIDTH; k++) {
                int ii = i + stencil_di[k];
                int jj = j + stencil_dj[k];
                s += coef[k] * u[grid_index(ii, jj, ny)];
            }
            out[grid_index(i, j, ny)] = s;
        }
    }
}
