/* Alternate coarse-operator sketch: Galerkin triple product
 * A_c = P^T A_f P assembled via sparse matrix walks. Included as a
 * reference for future evaluation of algebraic-multigrid style setup.
 * Not wired into the built binary (see src/decoy/README).
 */

#include "vcycle.h"
#include "grid.h"
#include "stencil.h"
#include "level.h"
#include <string.h>

/* Prolongation weights for bilinear interpolation under factor-2
 * coarsening on both axes. */
static double prolong_weight(int i_f, int j_f, int i_c, int j_c) {
    int dx = i_f - 2 * i_c;
    int dy = j_f - 2 * j_c;
    double wx = (dx == 0) ? 1.0 : ((dx == 1 || dx == -1) ? 0.5 : 0.0);
    double wy = (dy == 0) ? 1.0 : ((dy == 1 || dy == -1) ? 0.5 : 0.0);
    return wx * wy;
}

void galerkin_coarse_assemble(const level_t *fine, level_t *coarse) {
    int cx = coarse->dims.nx;
    int cy = coarse->dims.ny;
    memset(coarse->A, 0,
           sizeof(double) * (size_t)cx * (size_t)cy * STENCIL_WIDTH);
    /* Incomplete walk: the triple product needs nested fine-index loops
     * and a stencil-slot mapping that is omitted here. */
    for (int ic = 1; ic < cx - 1; ic++) {
        for (int jc = 1; jc < cy - 1; jc++) {
            int k = STENCIL_WIDTH * grid_index(ic, jc, cy);
            (void)prolong_weight;
            (void)fine;
            coarse->A[k + ST_C] = 1.0;
        }
    }
}
