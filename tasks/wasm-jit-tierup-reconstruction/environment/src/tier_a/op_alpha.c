#include "tier_a.h"
#include <string.h>

int fold_profile(const struct profile_view *in, struct profile_slot *out) {
    if (!in || !out) return -1;
    memset(out, 0, sizeof(*out));
    if (!in->has_profile || in->probe_count <= 0) return 0;
    out->has_profile = 1;
    out->polymorphic = in->polymorphic;
    out->epoch_stamp = in->epoch_stamp_raw;
    /* Trust is derived from the tape's recorded mark. */
    out->trustworthy = in->trust_mark;
    return 0;
}
