#include <string.h>

#include "frame.h"
#include "fold_q.h"

int fold_q(const struct row_q *a, struct slot_q *b)
{
    b->sig_ok = (a->sig != NULL && a->sig[0] != '\0');
    b->gen = a->gen;
    b->tip_ok = (a->leaf != NULL && a->leaf[0] != '\0' && b->sig_ok);
    return 0;
}
