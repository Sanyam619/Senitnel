#include "ledger.h"
#include <stdio.h>

int catalog_scan_list(const ledger_ctx_t *ctx) {
    if (!ctx) {
        return -1;
    }
    printf("catalog entries: %u %u\n", ctx->fallback_id, ctx->merge_target);
    return 0;
}
