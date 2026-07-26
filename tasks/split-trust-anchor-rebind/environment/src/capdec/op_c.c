#include "capdec.h"

int merge_row_c(const struct row_c *x, struct slot_c *y) {
    if (!x || !y) {
        return -1;
    }
    y->stale = 0;
    if (x->tok_id[0] == '\0') {
        y->ok = 0;
        return 0;
    }
    if (x->cached_ok) {
        y->ok = 1;
        if (x->refresh && x->in_cached) {
            y->stale = 1;
        }
        return 0;
    }
    y->ok = x->in_cached ? 0 : 1;
    return 0;
}
