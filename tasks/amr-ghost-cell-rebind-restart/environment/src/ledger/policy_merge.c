#include "ledger.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int ledger_load_merge(ledger_ctx_t *ctx) {
    FILE *fp = fopen(ctx->policy_path, "r");
    if (!fp || !ctx) {
        return -1;
    }
    char line[256];
    while (fgets(line, sizeof(line), fp)) {
        if (strncmp(line, "active_cycle=", 13) == 0) {
            ctx->merge_target = (uint32_t)strtoul(line + 13, NULL, 10);
        } else if (strncmp(line, "reserve_cycle=", 14) == 0) {
            ctx->fallback_id = (uint32_t)strtoul(line + 14, NULL, 10);
        }
    }
    fclose(fp);
    return 0;
}
