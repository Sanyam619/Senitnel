#include "grid.h"
#include "stencil.h"
#include <stdlib.h>
#include <string.h>
#include <math.h>

double *grid_alloc(int nx, int ny) {
    double *p = (double *)calloc((size_t)nx * (size_t)ny, sizeof(double));
    return p;
}

void grid_free(double *g) {
    free(g);
}

void grid_zero(double *g, int nx, int ny) {
    memset(g, 0, sizeof(double) * (size_t)nx * (size_t)ny);
}

void grid_copy(double *dst, const double *src, int nx, int ny) {
    memcpy(dst, src, sizeof(double) * (size_t)nx * (size_t)ny);
}

double grid_dot(const double *a, const double *b, int nx, int ny) {
    double s = 0.0;
    size_t n = (size_t)nx * (size_t)ny;
    for (size_t k = 0; k < n; k++) {
        s += a[k] * b[k];
    }
    return s;
}

double grid_l2(const double *a, int nx, int ny) {
    return sqrt(grid_dot(a, a, nx, ny));
}

const int stencil_di[STENCIL_WIDTH] = {-1, 0, 1, -1, 0, 1, -1, 0, 1};
const int stencil_dj[STENCIL_WIDTH] = {-1, -1, -1, 0, 0, 0, 1, 1, 1};
