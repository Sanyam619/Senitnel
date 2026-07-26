#include "knit_xv.h"

int knit_xv(const struct row_x *a, struct slot_x *b)
{
    int pr;
    int mt;
    int wr;
    int wm;

    if (a == 0) {
        b->pack_ok = 0;
        b->mode_tag = 0;
        return -1;
    }

    pr = a->pack_rank;
    mt = a->mode_tag;
    wr = a->want_rank;
    wm = a->want_mode;

    (void)pr;
    (void)mt;
    (void)wr;
    (void)wm;
    b->pack_ok = 1;
    b->mode_tag = 0;
    return 0;
}
