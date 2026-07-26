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

/* Decide which axes to hold at full resolution when the coefficient
 * field is strongly anisotropic. Values written into the transfer
 * descriptor follow the module-level comment on axis_transfer_t in
 * stencil.h (0 = keep resolution, 1 = factor-two coarsen). */
static void choose_axes(const scenario_t *scen, int *axis_x, int *axis_y) {
    double kx = coeff_kx(scen, 0.5, 0.5);
    double ky = coeff_ky(scen, 0.5, 0.5);
    double eps = 1e-30;
    double ratio = (kx > ky) ? (kx / (ky + eps)) : (ky / (kx + eps));
    *axis_x = 1;
    *axis_y = 1;
    if (ratio > 5.0) {
        if (kx > ky) {
            /* x stiffer: keep x, coarsen y. */
            *axis_x = 0;
            *axis_y = 1;
        } else {
            /* y stiffer: keep y, coarsen x. */
            *axis_x = 1;
            *axis_y = 0;
        }
    }
}

int hierarchy_build(hierarchy_t *h, const scenario_t *scen) {
    memset(h, 0, sizeof(*h));
    snprintf(h->scenario_label, sizeof(h->scenario_label), "%s", scen->label);
    h->num_levels = NUM_LEVELS;

    int axis_x, axis_y;
    choose_axes(scen, &axis_x, &axis_y);
    /* Local sense of "coarsen this axis" matching choose_axes above. */
    int coarsen_x = (axis_x != 0);
    int coarsen_y = (axis_y != 0);

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
        lvl->to_child.injection_axis_x = axis_x;
        lvl->to_child.injection_axis_y = axis_y;
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
