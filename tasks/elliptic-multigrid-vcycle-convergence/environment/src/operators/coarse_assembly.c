#include "vcycle.h"
#include "grid.h"
#include "stencil.h"
#include "level.h"
#include <stdlib.h>
#include <string.h>

/* Recover face conductivity from a fine stencil entry. Fine assembly
 * stores A[slot] = -k_face / h_face^2. */
static inline double fine_face_k(const level_t *fine, int i, int j,
                                 int slot, double h_face_sq) {
    double a = fine->A[STENCIL_WIDTH * grid_index(i, j, fine->dims.ny) + slot];
    return -a * h_face_sq;
}

/* Combine two fine-face conductivities that span one coarse face. */
static inline double combine_k(double k1, double k2) {
    return 0.5 * (k1 + k2);
}

void coarse_operator_assemble(const level_t *fine, level_t *coarse) {
    int cx = coarse->dims.nx;
    int cy = coarse->dims.ny;
    double h_fx = fine->dims.hx;
    double h_fy = fine->dims.hy;
    double h_fx_sq = h_fx * h_fx;
    double h_fy_sq = h_fy * h_fy;
    int coarsen_x = (fine->to_child.injection_axis_x == 0) ? 1 : 0;
    int coarsen_y = (fine->to_child.injection_axis_y == 0) ? 1 : 0;

    double h_cx = coarsen_x ? 2.0 * h_fx : h_fx;
    double h_cy = coarsen_y ? 2.0 * h_fy : h_fy;
    coarse->dims.hx = h_cx;
    coarse->dims.hy = h_cy;

    memset(coarse->A, 0,
           sizeof(double) * (size_t)cx * (size_t)cy * STENCIL_WIDTH);

    for (int ic = 0; ic < cx; ic++) {
        for (int jc = 0; jc < cy; jc++) {
            if (ic == 0 || ic == cx - 1 || jc == 0 || jc == cy - 1) {
                int base = STENCIL_WIDTH * grid_index(ic, jc, cy);
                coarse->A[base + ST_C] = 1.0;
            }
        }
    }

    for (int ic = 1; ic < cx - 1; ic++) {
        int i_c = coarsen_x ? 2 * ic : ic;
        for (int jc = 1; jc < cy - 1; jc++) {
            int j_c = coarsen_y ? 2 * jc : jc;

            double kE, kW, kN, kS;
            if (coarsen_x) {
                kE = combine_k(fine_face_k(fine, i_c,     j_c, ST_E, h_fx_sq),
                               fine_face_k(fine, i_c + 1, j_c, ST_E, h_fx_sq));
                kW = combine_k(fine_face_k(fine, i_c,     j_c, ST_W, h_fx_sq),
                               fine_face_k(fine, i_c - 1, j_c, ST_W, h_fx_sq));
            } else {
                kE = fine_face_k(fine, i_c, j_c, ST_E, h_fx_sq);
                kW = fine_face_k(fine, i_c, j_c, ST_W, h_fx_sq);
            }
            if (coarsen_y) {
                kN = combine_k(fine_face_k(fine, i_c, j_c,     ST_N, h_fy_sq),
                               fine_face_k(fine, i_c, j_c + 1, ST_N, h_fy_sq));
                kS = combine_k(fine_face_k(fine, i_c, j_c,     ST_S, h_fy_sq),
                               fine_face_k(fine, i_c, j_c - 1, ST_S, h_fy_sq));
            } else {
                kN = fine_face_k(fine, i_c, j_c, ST_N, h_fy_sq);
                kS = fine_face_k(fine, i_c, j_c, ST_S, h_fy_sq);
            }

            /* Scale stencil coefficients with the fine spacing so the
             * rediscretised operator keeps the same local magnitude as
             * neighbouring fine rows. */
            double aE = kE / (h_fx * h_fx);
            double aW = kW / (h_fx * h_fx);
            double aN = kN / (h_fy * h_fy);
            double aS = kS / (h_fy * h_fy);

            double *row = &coarse->A[STENCIL_WIDTH * grid_index(ic, jc, cy)];
            row[ST_E] = -aE;
            row[ST_W] = -aW;
            row[ST_N] = -aN;
            row[ST_S] = -aS;
            row[ST_C] = aE + aW + aN + aS;
        }
    }
}
