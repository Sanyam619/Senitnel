#include "vcycle.h"
#include "grid.h"

void residual_compute(const level_t *lvl, const double *u,
                      const double *f, double *r) {
    int nx = lvl->dims.nx;
    int ny = lvl->dims.ny;
    stencil_apply(lvl, u, r);
    for (int i = 0; i < nx; i++) {
        for (int j = 0; j < ny; j++) {
            int k = grid_index(i, j, ny);
            if (i == 0 || i == nx - 1 || j == 0 || j == ny - 1) {
                r[k] = 0.0;
            } else {
                r[k] = f[k] - r[k];
            }
        }
    }
}
