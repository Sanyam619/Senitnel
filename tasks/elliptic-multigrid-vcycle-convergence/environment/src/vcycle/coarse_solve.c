#include "vcycle.h"
#include "grid.h"
#include "stencil.h"
#include <stdlib.h>
#include <string.h>
#include <math.h>

/* Direct LU with partial pivoting for the coarsest-level linear
 * system. The interior nodes are packed into a dense (n_int x n_int)
 * matrix using the 9-point stencil. Called once per hierarchy build. */

static int interior_count(const level_t *lvl) {
    return (lvl->dims.nx - 2) * (lvl->dims.ny - 2);
}

static int interior_idx(int i, int j, int ny_int) {
    return (i - 1) * ny_int + (j - 1);
}

int coarse_solve_prepare(level_t *lvl) {
    int nx = lvl->dims.nx;
    int ny = lvl->dims.ny;
    int n_int = interior_count(lvl);
    int ny_int = ny - 2;
    if (lvl->lu_A) free(lvl->lu_A);
    if (lvl->piv) free(lvl->piv);
    lvl->lu_A = (double *)calloc((size_t)n_int * (size_t)n_int, sizeof(double));
    lvl->piv = (int *)calloc((size_t)n_int, sizeof(int));
    lvl->lu_dim = n_int;
    if (!lvl->lu_A || !lvl->piv) return -1;

    double *M = lvl->lu_A;

    for (int i = 1; i < nx - 1; i++) {
        for (int j = 1; j < ny - 1; j++) {
            int row = interior_idx(i, j, ny_int);
            const double *coef = &lvl->A[STENCIL_WIDTH * grid_index(i, j, ny)];
            for (int k = 0; k < STENCIL_WIDTH; k++) {
                int ii = i + stencil_di[k];
                int jj = j + stencil_dj[k];
                if (ii <= 0 || ii >= nx - 1 || jj <= 0 || jj >= ny - 1) continue;
                int col = interior_idx(ii, jj, ny_int);
                M[row * n_int + col] += coef[k];
            }
        }
    }

    /* LU decomposition with partial pivoting on M. */
    for (int k = 0; k < n_int; k++) {
        /* Find pivot row. */
        int p = k;
        double amax = fabs(M[k * n_int + k]);
        for (int r = k + 1; r < n_int; r++) {
            double v = fabs(M[r * n_int + k]);
            if (v > amax) {
                amax = v;
                p = r;
            }
        }
        lvl->piv[k] = p;
        if (p != k) {
            for (int c = 0; c < n_int; c++) {
                double t = M[k * n_int + c];
                M[k * n_int + c] = M[p * n_int + c];
                M[p * n_int + c] = t;
            }
        }
        double pivot = M[k * n_int + k];
        if (pivot == 0.0) return -1;
        for (int r = k + 1; r < n_int; r++) {
            double lrk = M[r * n_int + k] / pivot;
            M[r * n_int + k] = lrk;
            for (int c = k + 1; c < n_int; c++) {
                M[r * n_int + c] -= lrk * M[k * n_int + c];
            }
        }
    }
    return 0;
}

void coarse_solve_apply(const level_t *lvl, const double *f, double *u) {
    int nx = lvl->dims.nx;
    int ny = lvl->dims.ny;
    int ny_int = ny - 2;
    int n_int = lvl->lu_dim;
    double *b = (double *)calloc((size_t)n_int, sizeof(double));
    if (!b) return;

    for (int i = 1; i < nx - 1; i++) {
        for (int j = 1; j < ny - 1; j++) {
            b[interior_idx(i, j, ny_int)] = f[grid_index(i, j, ny)];
        }
    }

    /* Apply pivot permutation, then forward/back substitution. */
    for (int k = 0; k < n_int; k++) {
        int p = lvl->piv[k];
        if (p != k) {
            double t = b[k];
            b[k] = b[p];
            b[p] = t;
        }
    }
    for (int r = 1; r < n_int; r++) {
        double s = b[r];
        for (int c = 0; c < r; c++) {
            s -= lvl->lu_A[r * n_int + c] * b[c];
        }
        b[r] = s;
    }
    for (int r = n_int - 1; r >= 0; r--) {
        double s = b[r];
        for (int c = r + 1; c < n_int; c++) {
            s -= lvl->lu_A[r * n_int + c] * b[c];
        }
        b[r] = s / lvl->lu_A[r * n_int + r];
    }

    grid_zero(u, nx, ny);
    for (int i = 1; i < nx - 1; i++) {
        for (int j = 1; j < ny - 1; j++) {
            u[grid_index(i, j, ny)] = b[interior_idx(i, j, ny_int)];
        }
    }
    free(b);
}
