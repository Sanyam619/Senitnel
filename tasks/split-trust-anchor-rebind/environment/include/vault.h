#ifndef VAULT_H
#define VAULT_H

#include "common.h"

int load_store_meta(uint32_t *live_gen, uint32_t *restore_gen);
int merge_row_a(const struct row_a *x, struct slot_a *y);
int scan_roots(char *out, size_t n);

#endif
