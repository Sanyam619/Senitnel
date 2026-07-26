#include "klb_types.h"
#include <string.h>

int op_weave(const char *path, KlbWeave *out);
int op_latch(const KlbWeave *w, KlbLatch *out);

int stage_a(const char *trace, KlbWeave *w, KlbLatch *l, char missed[32]) {
    if (op_weave(trace, w) != 0) return -1;
    KlbWeave snap = *w;
    snap.miss_ts = 0;
    if (op_latch(&snap, l) != 0) return -1;
    strncpy(missed, w->missed, 31);
    return 0;
}
