#ifndef STENCIL_H
#define STENCIL_H

/* Nine-point stencil layout used uniformly at every level of the
 * hierarchy. For a fine 5-point operator the corner slots are zero;
 * for the coarse operators produced by Galerkin projection the corner
 * slots carry the cross-coupling weights that the coarsening naturally
 * introduces.
 *
 * The nine entries at cell (i, j) are packed contiguously as
 *   A[9 * grid_index(i, j, ny) + k]  for k = 0..8
 * with the (di, dj) offsets given below.
 */

#define ST_SW 0  /* (-1, -1) */
#define ST_S  1  /* ( 0, -1) */
#define ST_SE 2  /* ( 1, -1) */
#define ST_W  3  /* (-1,  0) */
#define ST_C  4  /* ( 0,  0)  center / diagonal */
#define ST_E  5  /* ( 1,  0) */
#define ST_NW 6  /* (-1,  1) */
#define ST_N  7  /* ( 0,  1) */
#define ST_NE 8  /* ( 1,  1) */

#define STENCIL_WIDTH 9

extern const int stencil_di[STENCIL_WIDTH];
extern const int stencil_dj[STENCIL_WIDTH];

/* Table entries for building coarse operators via the two commonly used
 * bilinear restriction / prolongation stencils. `injection_axis` = 0
 * means the axis is not coarsened at this level (indices copy through
 * without averaging); = 1 means factor-two coarsening with linear
 * weights (1/2, 1, 1/2) for restriction / prolongation on that axis. */
typedef struct axis_transfer {
    int injection_axis_x; /* 0 = coarsen x, 1 = keep x resolution */
    int injection_axis_y; /* 0 = coarsen y, 1 = keep y resolution */
} axis_transfer_t;

#endif /* STENCIL_H */
