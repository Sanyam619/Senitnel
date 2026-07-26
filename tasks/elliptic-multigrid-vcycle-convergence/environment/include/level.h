#ifndef LEVEL_H
#define LEVEL_H

#include "grid.h"
#include "stencil.h"
#include "scenario.h"

typedef struct level {
    grid_dims_t dims;
    double *A;      /* stencil coefficients, size nx * ny * STENCIL_WIDTH */
    double *u;      /* current iterate */
    double *f;      /* right-hand side */
    double *r;      /* working residual buffer */
    double omega;   /* smoother weight applied on this level */
    axis_transfer_t to_child; /* how this level restricts to the next coarser level */
    /* Coarse-solve factorization data (populated only on the coarsest
     * level; each other level leaves lu_A / piv NULL). */
    double *lu_A;
    int *piv;
    int lu_dim;
} level_t;

typedef struct hierarchy {
    int num_levels;
    level_t levels[8]; /* NUM_LEVELS <= 8 */
    char scenario_label[SCENARIO_LABEL_MAX];
} hierarchy_t;

int hierarchy_build(hierarchy_t *h, const scenario_t *scen);
void hierarchy_free(hierarchy_t *h);

#endif /* LEVEL_H */
