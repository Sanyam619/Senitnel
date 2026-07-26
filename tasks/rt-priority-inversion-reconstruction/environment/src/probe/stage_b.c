#include "klb_types.h"

int op_span(const KlbLatch *l, const char *tgt, char chain[3][32]);
int op_lift(const char *cfg, const char *tgt, int *ceilings, int cap);

int stage_b(const char *cfg, const KlbLatch *l, const char *tgt, char chain[3][32], int *ceilings, int *n_ceil) {
    if (op_span(l, tgt, chain) != 0) return -1;
    *n_ceil = op_lift(cfg, tgt, ceilings, 8);
    return 0;
}
