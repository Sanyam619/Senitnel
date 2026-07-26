#include "klb_types.h"
#include <string.h>

int filter_gate_rows(KlbWeave *w) {
    int out = 0;
    for (int i = 0; i < w->n_gate; i++) {
        if (!w->gate[i].is_wait) {
            w->gate[out++] = w->gate[i];
        }
    }
    w->n_gate = out;
    return 0;
}
