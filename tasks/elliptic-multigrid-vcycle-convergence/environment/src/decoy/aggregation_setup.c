/* Alternate level construction sketch: algebraic aggregation.
 * Groups fine-grid nodes into small clusters and derives the coarse
 * hierarchy from an aggregation graph instead of geometric coarsening.
 * Not wired into the built binary (see src/decoy/README). */

#include "vcycle.h"
#include "level.h"
#include "grid.h"
#include "scenario.h"
#include <stdlib.h>

/* Assign each fine node to a cluster id. Draft pairing uses 2x2
 * blocks. Real aggregation would use strength-of-connection weights
 * from the fine operator. */
int aggregation_build(const level_t *fine, int *cluster_id) {
    int nx = fine->dims.nx;
    int ny = fine->dims.ny;
    int nc_x = (nx + 1) / 2;
    for (int i = 0; i < nx; i++) {
        for (int j = 0; j < ny; j++) {
            int ci = i / 2;
            int cj = j / 2;
            cluster_id[grid_index(i, j, ny)] = cj * nc_x + ci;
        }
    }
    return nc_x * ((ny + 1) / 2);
}
