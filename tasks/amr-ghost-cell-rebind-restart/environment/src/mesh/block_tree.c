#include "mesh.h"

int mesh_reconcile_layout(mesh_ctx_t *m, uint32_t gen_id) {
    if (!m) {
        return -1;
    }
    (void)gen_id;
    m->layout_ready = 1;
    m->links_ready = 0;
    m->link_gen = 0;
    return 0;
}
