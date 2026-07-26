#ifndef MESH_H
#define MESH_H

#include <stdint.h>

typedef struct mesh_ctx {
    int block_tally;
    int tree_depth;
    uint32_t link_gen;
    int links_ready;
    int layout_ready;
} mesh_ctx_t;

int mesh_load_policy(const char *path, const char *label, mesh_ctx_t *m);
int mesh_reconcile_layout(mesh_ctx_t *m, uint32_t gen_id);
int mesh_adj_refresh(mesh_ctx_t *m, uint32_t gen_id);
uint32_t mesh_coupling_tag(const mesh_ctx_t *m, uint32_t g, uint32_t canon);

#endif
