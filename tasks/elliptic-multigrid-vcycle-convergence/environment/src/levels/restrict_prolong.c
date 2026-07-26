#include "vcycle.h"
#include "grid.h"
#include "stencil.h"
#include <string.h>

/* Full-weighting restriction and bilinear prolongation that dispatch on
 * the fine level's axis-transfer descriptor. When `injection_axis_*` is
 * set, the corresponding axis is treated as injection (fine and coarse
 * share resolution on that axis); otherwise factor-two coarsening with
 * the (1, 2, 1) / 4 weights is applied. */

static const int OFF3[3] = {-1, 0, 1};
static const double W3[3] = {1.0, 2.0, 1.0};

static inline int in_bounds(int i, int j, int nx, int ny) {
    return (i >= 0 && i < nx && j >= 0 && j < ny);
}

void restrict_full_weight(const level_t *fine, const level_t *coarse,
                          const double *fine_field, double *coarse_field) {
    int cx = coarse->dims.nx;
    int cy = coarse->dims.ny;
    int fx = fine->dims.nx;
    int fy = fine->dims.ny;
    int coarsen_x = (fine->to_child.injection_axis_x == 0) ? 1 : 0;
    int coarsen_y = (fine->to_child.injection_axis_y == 0) ? 1 : 0;

    for (int ic = 0; ic < cx; ic++) {
        int i_center = coarsen_x ? 2 * ic : ic;
        for (int jc = 0; jc < cy; jc++) {
            int j_center = coarsen_y ? 2 * jc : jc;
            if (ic == 0 || ic == cx - 1 || jc == 0 || jc == cy - 1) {
                coarse_field[grid_index(ic, jc, cy)] = 0.0;
                continue;
            }
            double sum = 0.0;
            double wsum = 0.0;
            int i_lo = coarsen_x ? 0 : 1;
            int i_hi = coarsen_x ? 3 : 2;
            int j_lo = coarsen_y ? 0 : 1;
            int j_hi = coarsen_y ? 3 : 2;
            for (int a = i_lo; a < i_hi; a++) {
                int i_f = i_center + (coarsen_x ? OFF3[a] : 0);
                double wa = coarsen_x ? W3[a] : 1.0;
                for (int b = j_lo; b < j_hi; b++) {
                    int j_f = j_center + (coarsen_y ? OFF3[b] : 0);
                    double wb = coarsen_y ? W3[b] : 1.0;
                    if (!in_bounds(i_f, j_f, fx, fy)) continue;
                    double w = wa * wb;
                    sum += w * fine_field[grid_index(i_f, j_f, fy)];
                    wsum += w;
                }
            }
            /* Full-weighting normalisation. The 1-D (1,2,1) stencil
             * sums to 4; use that factor regardless of how many axes
             * are being coarsened so the restricted residual keeps a
             * comparable magnitude on semi-coarsened levels. */
            double denom = 4.0;
            coarse_field[grid_index(ic, jc, cy)] = sum / denom;
            (void)wsum;
            (void)coarsen_x;
            (void)coarsen_y;
        }
    }
}

void prolongate_bilinear_add(const level_t *fine, const level_t *coarse,
                             const double *coarse_field, double *fine_field) {
    int cx = coarse->dims.nx;
    int cy = coarse->dims.ny;
    int fx = fine->dims.nx;
    int fy = fine->dims.ny;
    int coarsen_x = (fine->to_child.injection_axis_x == 0) ? 1 : 0;
    int coarsen_y = (fine->to_child.injection_axis_y == 0) ? 1 : 0;

    for (int i_f = 1; i_f < fx - 1; i_f++) {
        int ic0, ic1;
        double wx0, wx1;
        if (coarsen_x) {
            ic0 = i_f / 2;
            if (i_f % 2 == 0) {
                ic1 = ic0;
                wx0 = 1.0;
                wx1 = 0.0;
            } else {
                ic1 = ic0 + 1;
                wx0 = 0.5;
                wx1 = 0.5;
            }
        } else {
            ic0 = ic1 = i_f;
            wx0 = 1.0;
            wx1 = 0.0;
        }
        if (ic0 < 0 || ic0 >= cx || ic1 < 0 || ic1 >= cx) continue;
        for (int j_f = 1; j_f < fy - 1; j_f++) {
            int jc0, jc1;
            double wy0, wy1;
            if (coarsen_y) {
                jc0 = j_f / 2;
                if (j_f % 2 == 0) {
                    jc1 = jc0;
                    wy0 = 1.0;
                    wy1 = 0.0;
                } else {
                    jc1 = jc0 + 1;
                    wy0 = 0.5;
                    wy1 = 0.5;
                }
            } else {
                jc0 = jc1 = j_f;
                wy0 = 1.0;
                wy1 = 0.0;
            }
            if (jc0 < 0 || jc0 >= cy || jc1 < 0 || jc1 >= cy) continue;
            double interp =
                wx0 * wy0 * coarse_field[grid_index(ic0, jc0, cy)] +
                wx1 * wy0 * coarse_field[grid_index(ic1, jc0, cy)] +
                wx0 * wy1 * coarse_field[grid_index(ic0, jc1, cy)] +
                wx1 * wy1 * coarse_field[grid_index(ic1, jc1, cy)];
            fine_field[grid_index(i_f, j_f, fy)] += interp;
        }
    }
}
