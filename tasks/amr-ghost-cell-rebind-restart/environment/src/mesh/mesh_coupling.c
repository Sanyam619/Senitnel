#include "mesh.h"

uint32_t mesh_coupling_tag(const mesh_ctx_t *m, uint32_t g, uint32_t canon) {
    uint32_t t = 0;
    t |= (uint32_t)(m->layout_ready & 1);
    t |= (uint32_t)(m->links_ready & 1) << 1;
    t |= (uint32_t)((m->link_gen == g) ? 1u : 0u) << 2;
    t |= (uint32_t)((g == canon) ? 1u : 0u) << 3;
    return t;
}
