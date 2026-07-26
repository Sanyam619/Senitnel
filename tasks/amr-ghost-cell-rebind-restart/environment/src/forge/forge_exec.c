#include "forge.h"
#include "ledger.h"
#include "mesh.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

extern int forge_attach_fields(forge_ctx_t *ctx, mesh_ctx_t *mesh);

static const int k_s0 = 1;
static const int k_s1 = 2;
static const int k_s2 = 4;

static int run_bit(forge_ctx_t *ctx, mesh_ctx_t *mesh, int bit) {
    if (bit == k_s0) {
        return mesh_reconcile_layout(mesh, ctx->gen_id);
    }
    if (bit == k_s1) {
        return mesh_adj_refresh(mesh, ctx->gen_id);
    }
    if (bit == k_s2) {
        return forge_attach_fields(ctx, mesh);
    }
    return 0;
}

int forge_exec_ring(forge_ctx_t *ctx, int stage_mask) {
    if (!ctx) {
        return -1;
    }
    mesh_ctx_t mesh = {0};
    mesh_load_policy(ctx->policy_path, ctx->scenario, &mesh);

    int order[8];
    size_t n = forge_stage_order(order, sizeof(order) / sizeof(order[0]));
    for (size_t i = 0; i < n; i++) {
        int bit = order[i];
        if ((stage_mask & bit) == 0) {
            continue;
        }
        if (run_bit(ctx, &mesh, bit) != 0) {
            return -1;
        }
        ctx->stages_done |= bit;
    }
    ctx->block_tally = mesh.block_tally;
    ctx->tree_depth = mesh.tree_depth;
    return 0;
}

int forge_run_recover(forge_ctx_t *ctx) {
    if (!ctx) {
        return -1;
    }
    ledger_ctx_t ledger = {.policy_path = ctx->policy_path};
    if (ledger_load_merge(&ledger) != 0) {
        return -1;
    }
    ctx->merge_target = ledger.merge_target;
    if (ledger_row_bind(&ledger, &ctx->gen_id) != 0) {
        return -1;
    }
    return forge_exec_ring(ctx, forge_stage_mask());
}
