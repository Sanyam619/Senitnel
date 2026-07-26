#include "klb_types.h"
#include <stdio.h>

void dump_shadow(const KlbLatch *l) {
    if (!l) return;
    fprintf(stderr, "shadow running=%s holder=%s\n", l->running, l->holder[0]);
}
