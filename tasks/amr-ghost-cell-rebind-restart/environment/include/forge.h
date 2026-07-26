#ifndef FORGE_H
#define FORGE_H

#include <stdint.h>
#include <stddef.h>

typedef struct forge_ctx {
    char scenario[64];
    const char *policy_path;
    const char *fixture_path;
    int stages_done;
    uint32_t gen_id;
    uint32_t merge_target;
    float face_l2;
    float mass_drift;
    int block_tally;
    int tree_depth;
} forge_ctx_t;

#define RESTART_JSON_TAG "amr-rs-v1"
#define RESTART_DRIFT_CAP 0.01f
#define RESTART_FACE_CAP 0.001f

int forge_stage_mask(void);
size_t forge_stage_order(int *out, size_t cap);
int forge_exec_ring(forge_ctx_t *ctx, int stage_mask);
int forge_run_recover(forge_ctx_t *ctx);

#endif
