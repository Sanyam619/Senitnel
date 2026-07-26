#include "vcycle.h"
#include "grid.h"
#include "stencil.h"
#include "scenario.h"
#include <string.h>

/* Assemble the fine-grid five-point stencil for the variable-coefficient
 * elliptic operator -div(k * grad(u)) on a uniform node-centered grid.
 * Interior node (i, j) accumulates contributions from face conductivities
 * derived from the scenario coefficient laws. The discretisation scales
 * as k_face / h^2. Corner slots (SW/SE/NW/NE) of the 9-point layout are
 * left at zero. Dirichlet boundary rows carry an identity row
 * (center = 1, others 0) so that boundary values remain fixed under
 * smoothing. */
void fine_operator_assemble(level_t *lvl, const scenario_t *scen) {
    int nx = lvl->dims.nx;
    int ny = lvl->dims.ny;
    double hx = lvl->dims.hx;
    double hy = lvl->dims.hy;
    memset(lvl->A, 0, sizeof(double) * (size_t)nx * (size_t)ny * STENCIL_WIDTH);

    for (int i = 0; i < nx; i++) {
        double x = i * hx;
        for (int j = 0; j < ny; j++) {
            double y = j * hy;
            double *coef = &lvl->A[STENCIL_WIDTH * grid_index(i, j, ny)];
            if (i == 0 || i == nx - 1 || j == 0 || j == ny - 1) {
                coef[ST_C] = 1.0;
                continue;
            }
            /* Face conductivities sampled at the neighbouring nodes and
             * averaged. For smooth coefficient fields this is equivalent
             * to a mid-face sample; for discontinuous k it blends across
             * the jump. */
            double kxE = 0.5 * (coeff_kx(scen, x, y) + coeff_kx(scen, x + hx, y));
            double kxW = 0.5 * (coeff_kx(scen, x, y) + coeff_kx(scen, x - hx, y));
            double kyN = 0.5 * (coeff_ky(scen, x, y) + coeff_ky(scen, x, y + hy));
            double kyS = 0.5 * (coeff_ky(scen, x, y) + coeff_ky(scen, x, y - hy));
            double aE = kxE / (hx * hx);
            double aW = kxW / (hx * hx);
            double aN = kyN / (hy * hy);
            double aS = kyS / (hy * hy);
            coef[ST_E] = -aE;
            coef[ST_W] = -aW;
            coef[ST_N] = -aN;
            coef[ST_S] = -aS;
            coef[ST_C] = aE + aW + aN + aS;
        }
    }
}
