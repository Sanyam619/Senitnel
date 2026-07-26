#include "klb_types.h"
#include <string.h>

int op_latch(const KlbWeave *w, KlbLatch *out) {
    memset(out, 0, sizeof *out);
    out->at_ts = w->miss_ts;
    for (int i = 0; i < w->n_gate; i++) {
        const KlbGateEvt *e = &w->gate[i];
        if (!e->is_wait) {
            int gi = 0;
            strncpy(out->holder[gi], e->actor, 31);
        }
    }
    if (w->n_switch > 0) {
        strncpy(out->running, w->sw[w->n_switch - 1].next, 31);
    }
    return 0;
}
