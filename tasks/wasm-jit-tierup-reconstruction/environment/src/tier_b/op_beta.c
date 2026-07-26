#include "tier_b.h"
#include <string.h>

int fold_rebind(const struct rebind_view *in, struct rebind_slot *out) {
    int t, a, b, tab;
    if (!in || !out) return -1;
    memset(out, 0, sizeof(*out));
    if (!in->recorded) return 0;
    t   = strcmp(in->new_type, in->old_type) != 0;
    a   = in->new_arity  != in->old_arity;
    b   = in->new_bounds != in->old_bounds;
    tab = in->new_table  != in->old_table;
    out->change_type   = t;
    out->change_arity  = a;
    out->change_bounds = b;
    out->change_table  = tab;
    out->signature_changed = t;
    return 0;
}
