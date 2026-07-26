/* Alternate smoother sketch: red-black Gauss-Seidel with a
 * two-colour interior sweep. Kept as a reference for future
 * evaluation. Not wired into the built binary (see src/decoy/README). */

#include "vcycle.h"
#include "grid.h"
#include "stencil.h"
#include "level.h"

/* Two-colour sweep: colour 0 = (i + j) even, colour 1 = (i + j) odd. */
static void rb_sweep(level_t *lvl, int colour) {
    int nx = lvl->dims.nx;
    int ny = lvl->dims.ny;
    for (int i = 1; i < nx - 1; i++) {
        for (int j = 1; j < ny - 1; j++) {
            if (((i + j) & 1) != colour) continue;
            int k = grid_index(i, j, ny);
            const double *row = &lvl->A[STENCIL_WIDTH * k];
            double rhs = lvl->f[k];
            rhs -= row[ST_E] * lvl->u[grid_index(i + 1, j, ny)];
            rhs -= row[ST_W] * lvl->u[grid_index(i - 1, j, ny)];
            rhs -= row[ST_N] * lvl->u[grid_index(i, j + 1, ny)];
            rhs -= row[ST_S] * lvl->u[grid_index(i, j - 1, ny)];
            rhs -= row[ST_NE] * lvl->u[grid_index(i + 1, j + 1, ny)];
            rhs -= row[ST_NW] * lvl->u[grid_index(i - 1, j + 1, ny)];
            rhs -= row[ST_SE] * lvl->u[grid_index(i + 1, j - 1, ny)];
            rhs -= row[ST_SW] * lvl->u[grid_index(i - 1, j - 1, ny)];
            double d = row[ST_C];
            if (d != 0.0) lvl->u[k] = rhs / d;
        }
    }
}

void gauss_seidel_rb_smooth(level_t *lvl, int n_sweeps) {
    for (int s = 0; s < n_sweeps; s++) {
        rb_sweep(lvl, 0);
        rb_sweep(lvl, 1);
    }
}
