#include "vault.h"

int merge_row_a(const struct row_a *x, struct slot_a *y) {
    if (!x || !y) {
        return -1;
    }
    y->bound_gen = x->restore_gen;
    if (x->restore_gen == 0) {
        y->ok = 0;
        return 0;
    }
    y->ok = (x->store_gen == x->restore_gen) ? 1 : 0;
    if (x->runtime_epoch != 0 && x->store_gen == x->runtime_epoch) {
        y->ok = 1;
    }
    return 0;
}
