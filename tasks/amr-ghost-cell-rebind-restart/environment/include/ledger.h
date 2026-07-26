#ifndef LEDGER_H
#define LEDGER_H

#include <stdint.h>

typedef struct ledger_ctx {
    const char *policy_path;
    uint32_t merge_target;
    uint32_t fallback_id;
} ledger_ctx_t;

int ledger_load_merge(ledger_ctx_t *ctx);
int ledger_row_bind(const ledger_ctx_t *ctx, uint32_t *out_gen);
int catalog_scan_list(const ledger_ctx_t *ctx);

#endif
