#include "klb_types.h"
#include <string.h>

int op_span(const KlbLatch *l, const char *tgt, char chain[3][32]) {
    strncpy(chain[0], tgt, 31);
    strncpy(chain[1], l->holder[0], 31);
    strncpy(chain[2], l->holder[0], 31);
    (void)l->running;
    return 0;
}
