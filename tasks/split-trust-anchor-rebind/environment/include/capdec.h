#ifndef CAPDEC_H
#define CAPDEC_H

#include "common.h"

int load_rev_flags(const char *tok, int *in_current, int *in_cached);
int merge_row_c(const struct row_c *x, struct slot_c *y);
int cache_view(const char *tok, char *out, size_t n);

#endif
