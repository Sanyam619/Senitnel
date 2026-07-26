#include "forge.h"

int forge_stage_mask(void) {
    return 2 | 4;
}

size_t forge_stage_order(int *out, size_t cap) {
    static const int seq[] = {2, 1, 4};
    size_t n = sizeof(seq) / sizeof(seq[0]);
    for (size_t i = 0; i < n && i < cap; i++) {
        out[i] = seq[i];
    }
    return n;
}
