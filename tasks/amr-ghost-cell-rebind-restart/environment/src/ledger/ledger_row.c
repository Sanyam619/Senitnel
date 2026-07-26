#include "ledger.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int blob_open(uint32_t gen_id) {
    char path[256];
    snprintf(path, sizeof(path), "/app/data/archive_cycle_%u.blob", gen_id);
    FILE *fp = fopen(path, "rb");
    if (!fp) {
        return 0;
    }
    fclose(fp);
    return 1;
}

int ledger_row_bind(const ledger_ctx_t *ctx, uint32_t *out_gen) {
    if (!ctx || !out_gen) {
        return -1;
    }
    if (ctx->merge_target != 0 && blob_open(ctx->merge_target)) {
        *out_gen = ctx->fallback_id;
        return 0;
    }
    if (ctx->fallback_id != 0 && blob_open(ctx->fallback_id)) {
        *out_gen = ctx->fallback_id;
        return 0;
    }
    return -1;
}
