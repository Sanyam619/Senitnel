#ifndef GRID_H
#define GRID_H

#include <stddef.h>

/* Node-centered logically rectangular 2D grid.
 *
 * Indexing convention: g(i, j) = i * ny + j (X fastest is FALSE here,
 * Y is contiguous). Field-file dumps written by src/io/field_emit.c
 * respect the same layout.
 *
 * Dirichlet boundary rows (i == 0, i == nx - 1, j == 0, j == ny - 1)
 * hold prescribed values; only interior nodes are relaxed. */

typedef struct grid_dims {
    int nx;
    int ny;
    double hx; /* uniform x spacing */
    double hy; /* uniform y spacing */
} grid_dims_t;

static inline int grid_index(int i, int j, int ny) {
    return i * ny + j;
}

double *grid_alloc(int nx, int ny);
void grid_free(double *g);
void grid_zero(double *g, int nx, int ny);
void grid_copy(double *dst, const double *src, int nx, int ny);
double grid_dot(const double *a, const double *b, int nx, int ny);
double grid_l2(const double *a, int nx, int ny);

#endif /* GRID_H */
