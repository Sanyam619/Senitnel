#include "pinset.h"
#include <string.h>

int merge_row_b(const struct row_b *x, struct slot_b *y) {
    int subject_restore;
    int subject_active;
    int claim_active;

    if (!x || !y) {
        return -1;
    }
    subject_restore = (x->subject_lin[0] && x->restore_lin[0] &&
                       strcmp(x->subject_lin, x->restore_lin) == 0);
    subject_active = (x->subject_lin[0] && x->active_lin[0] &&
                      strcmp(x->subject_lin, x->active_lin) == 0);
    claim_active = (x->claim_lin[0] && x->active_lin[0] &&
                    strcmp(x->claim_lin, x->active_lin) == 0);

    y->used_restore = subject_restore ? 1 : 0;
    if (subject_restore) {
        y->ok = 1;
        return 0;
    }
    y->ok = (subject_active && claim_active) ? 1 : 0;
    return 0;
}
