#!/usr/bin/env bash
# Oracle solution for elliptic-multigrid-vcycle-convergence.
#
# Five interacting defects keep the shipped V-cycle from converging
# within budget across the scenario suite. Each looks like a plausible
# engineering choice in isolation; together they destroy the coarse-grid
# correction, the transfer scaling, the anisotropy policy, the fine
# face conductivities, and the smoother's ability to damp stiff modes.
set -euo pipefail
cd /app


# ---------------------------------------------------------------------------
# Fix 1: fine face conductivities evaluated at the face midpoints.
# ---------------------------------------------------------------------------
cat > src/operators/fine_assembly.c <<'CFILE'
#include "vcycle.h"
#include "grid.h"
#include "stencil.h"
#include "scenario.h"
#include <string.h>

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
            double kxE = coeff_kx(scen, x + 0.5 * hx, y);
            double kxW = coeff_kx(scen, x - 0.5 * hx, y);
            double kyN = coeff_ky(scen, x, y + 0.5 * hy);
            double kyS = coeff_ky(scen, x, y - 0.5 * hy);
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
CFILE

# ---------------------------------------------------------------------------
# Fix 2: coarse rediscretisation with series (harmonic) face combination
# and coarse-spacing scaling.
# ---------------------------------------------------------------------------
cat > src/operators/coarse_assembly.c <<'CFILE'
#include "vcycle.h"
#include "grid.h"
#include "stencil.h"
#include "level.h"
#include <stdlib.h>
#include <string.h>

static inline double fine_face_k(const level_t *fine, int i, int j,
                                 int slot, double h_face_sq) {
    double a = fine->A[STENCIL_WIDTH * grid_index(i, j, fine->dims.ny) + slot];
    return -a * h_face_sq;
}

static inline double series_k(double k1, double k2) {
    double eps = 1e-300;
    return 2.0 / (1.0 / (k1 + eps) + 1.0 / (k2 + eps));
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
                kE = series_k(fine_face_k(fine, i_c,     j_c, ST_E, h_fx_sq),
                              fine_face_k(fine, i_c + 1, j_c, ST_E, h_fx_sq));
                kW = series_k(fine_face_k(fine, i_c,     j_c, ST_W, h_fx_sq),
                              fine_face_k(fine, i_c - 1, j_c, ST_W, h_fx_sq));
            } else {
                kE = fine_face_k(fine, i_c, j_c, ST_E, h_fx_sq);
                kW = fine_face_k(fine, i_c, j_c, ST_W, h_fx_sq);
            }
            if (coarsen_y) {
                kN = series_k(fine_face_k(fine, i_c, j_c,     ST_N, h_fy_sq),
                              fine_face_k(fine, i_c, j_c + 1, ST_N, h_fy_sq));
                kS = series_k(fine_face_k(fine, i_c, j_c,     ST_S, h_fy_sq),
                              fine_face_k(fine, i_c, j_c - 1, ST_S, h_fy_sq));
            } else {
                kN = fine_face_k(fine, i_c, j_c, ST_N, h_fy_sq);
                kS = fine_face_k(fine, i_c, j_c, ST_S, h_fy_sq);
            }

            double aE = kE / (h_cx * h_cx);
            double aW = kW / (h_cx * h_cx);
            double aN = kN / (h_cy * h_cy);
            double aS = kS / (h_cy * h_cy);

            double *row = &coarse->A[STENCIL_WIDTH * grid_index(ic, jc, cy)];
            row[ST_E] = -aE;
            row[ST_W] = -aW;
            row[ST_N] = -aN;
            row[ST_S] = -aS;
            row[ST_C] = aE + aW + aN + aS;
        }
    }
}
CFILE

# ---------------------------------------------------------------------------
# Fix 3: transfer-descriptor polarity that matches restrict_prolong.c
# (injection_axis == 0 means coarsen), with semi-coarsening that holds
# the stiff axis.
# ---------------------------------------------------------------------------
cat > src/levels/level_policy.c <<'CFILE'
#include "vcycle.h"
#include "level.h"
#include "grid.h"
#include "stencil.h"
#include "scenario.h"
#include "solver_config.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int coarsen_dim(int n) {
    int nc = ((n - 1) / 2) + 1;
    return nc < 5 ? n : nc;
}

static void choose_axes(const scenario_t *scen, int *coarsen_x, int *coarsen_y) {
    double kx = coeff_kx(scen, 0.5, 0.5);
    double ky = coeff_ky(scen, 0.5, 0.5);
    double eps = 1e-30;
    double ratio = (kx > ky) ? (kx / (ky + eps)) : (ky / (kx + eps));
    *coarsen_x = 1;
    *coarsen_y = 1;
    if (ratio > 5.0) {
        if (kx > ky) {
            *coarsen_x = 0;
        } else {
            *coarsen_y = 0;
        }
    }
}

int hierarchy_build(hierarchy_t *h, const scenario_t *scen) {
    memset(h, 0, sizeof(*h));
    snprintf(h->scenario_label, sizeof(h->scenario_label), "%s", scen->label);
    h->num_levels = NUM_LEVELS;

    int coarsen_x, coarsen_y;
    choose_axes(scen, &coarsen_x, &coarsen_y);

    int nx = scen->nx;
    int ny = scen->ny;
    for (int L = 0; L < h->num_levels; L++) {
        level_t *lvl = &h->levels[L];
        lvl->dims.nx = nx;
        lvl->dims.ny = ny;
        lvl->dims.hx = 1.0 / (double)(nx - 1);
        lvl->dims.hy = 1.0 / (double)(ny - 1);
        lvl->A = (double *)calloc((size_t)nx * (size_t)ny * STENCIL_WIDTH,
                                   sizeof(double));
        lvl->u = grid_alloc(nx, ny);
        lvl->f = grid_alloc(nx, ny);
        lvl->r = grid_alloc(nx, ny);
        lvl->omega = 1.0;
        lvl->to_child.injection_axis_x = coarsen_x ? 0 : 1;
        lvl->to_child.injection_axis_y = coarsen_y ? 0 : 1;
        lvl->lu_A = NULL;
        lvl->piv = NULL;
        lvl->lu_dim = 0;
        if (!lvl->A || !lvl->u || !lvl->f || !lvl->r) return -1;

        if (L < h->num_levels - 1) {
            if (coarsen_x) nx = coarsen_dim(nx);
            if (coarsen_y) ny = coarsen_dim(ny);
        }
    }
    return 0;
}

void hierarchy_free(hierarchy_t *h) {
    for (int L = 0; L < h->num_levels; L++) {
        level_t *lvl = &h->levels[L];
        free(lvl->A); lvl->A = NULL;
        grid_free(lvl->u); lvl->u = NULL;
        grid_free(lvl->f); lvl->f = NULL;
        grid_free(lvl->r); lvl->r = NULL;
        free(lvl->lu_A); lvl->lu_A = NULL;
        free(lvl->piv); lvl->piv = NULL;
        lvl->lu_dim = 0;
    }
}
CFILE

# ---------------------------------------------------------------------------
# Fix 4: full-weighting denominator is 4^d where d is the number of
# coarsened axes.
# ---------------------------------------------------------------------------
cat > src/levels/restrict_prolong.c <<'CFILE'
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
            /* Divide by nominal weight sum (4 per coarsened axis). */
            double denom = 1.0;
            if (coarsen_x) denom *= 4.0;
            if (coarsen_y) denom *= 4.0;
            coarse_field[grid_index(ic, jc, cy)] = sum / denom;
            (void)wsum;
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
CFILE

# ---------------------------------------------------------------------------
# Fix 5: y-line Jacobi smoother with scenario-dependent under-relaxation.
# ---------------------------------------------------------------------------
cat > src/relaxation/weighted_jacobi.c <<'CFILE'
#include "vcycle.h"
#include "level.h"
#include "grid.h"
#include "stencil.h"
#include "scenario.h"
#include <stdlib.h>
#include <string.h>

static void tridiag_solve(int n, double *a, double *b, double *c, double *d) {
    for (int k = 1; k < n; k++) {
        double m = a[k] / b[k - 1];
        b[k] -= m * c[k - 1];
        d[k] -= m * d[k - 1];
    }
    d[n - 1] /= b[n - 1];
    for (int k = n - 2; k >= 0; k--) {
        d[k] = (d[k] - c[k] * d[k + 1]) / b[k];
    }
}

void weighted_jacobi_smooth(level_t *lvl, int n_sweeps) {
    int nx = lvl->dims.nx;
    int ny = lvl->dims.ny;
    int ni = ny - 2;
    if (ni <= 0) return;
    double omega = lvl->omega;
    double *a = (double *)malloc(sizeof(double) * (size_t)ni);
    double *b = (double *)malloc(sizeof(double) * (size_t)ni);
    double *c = (double *)malloc(sizeof(double) * (size_t)ni);
    double *d = (double *)malloc(sizeof(double) * (size_t)ni);
    if (!a || !b || !c || !d) { free(a); free(b); free(c); free(d); return; }

    for (int s = 0; s < n_sweeps; s++) {
        for (int i = 1; i < nx - 1; i++) {
            for (int j = 1; j < ny - 1; j++) {
                int k = grid_index(i, j, ny);
                const double *row = &lvl->A[STENCIL_WIDTH * k];
                int t = j - 1;
                a[t] = (j == 1)      ? 0.0 : row[ST_S];
                b[t] = row[ST_C];
                c[t] = (j == ny - 2) ? 0.0 : row[ST_N];
                double rhs = lvl->f[k];
                rhs -= row[ST_E] * lvl->u[grid_index(i + 1, j, ny)];
                rhs -= row[ST_W] * lvl->u[grid_index(i - 1, j, ny)];
                rhs -= row[ST_NE] * lvl->u[grid_index(i + 1, j + 1, ny)];
                rhs -= row[ST_NW] * lvl->u[grid_index(i - 1, j + 1, ny)];
                rhs -= row[ST_SE] * lvl->u[grid_index(i + 1, j - 1, ny)];
                rhs -= row[ST_SW] * lvl->u[grid_index(i - 1, j - 1, ny)];
                d[t] = rhs;
            }
            tridiag_solve(ni, a, b, c, d);
            for (int j = 1; j < ny - 1; j++) {
                int k = grid_index(i, j, ny);
                double u_new = d[j - 1];
                lvl->u[k] = (1.0 - omega) * lvl->u[k] + omega * u_new;
            }
        }
    }
    free(a); free(b); free(c); free(d);
}

double relax_weight_for(int level_idx, const scenario_t *scen) {
    (void)level_idx;
    if (!scen) return 1.0;
    if (strcmp(scen->label, "s_aniso") == 0)  return 1.0;
    if (strcmp(scen->label, "s_jump") == 0)   return 0.85;
    if (strcmp(scen->label, "s_corner") == 0) return 0.85;
    if (strcmp(scen->label, "s_mixed") == 0)  return 1.0;
    return 1.0;
}
CFILE

# ---------------------------------------------------------------------------
# Rebuild and run.
# ---------------------------------------------------------------------------
make clean
make
mkdir -p /app/output /app/output/traces /app/output/fields
/app/scripts/run_solve.sh
