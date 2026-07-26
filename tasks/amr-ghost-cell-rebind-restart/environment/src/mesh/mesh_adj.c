#include "mesh.h"

int mesh_adj_refresh(mesh_ctx_t *m, uint32_t gen_id) {
    if (!m) {
        return -1;
    }
    m->link_gen = gen_id;
    m->links_ready = 1;
    return 0;
}
