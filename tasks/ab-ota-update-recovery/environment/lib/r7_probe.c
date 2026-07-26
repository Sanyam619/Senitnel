#include "ab_api.h"
#include "ab_layout.h"

#include <stdio.h>

#include "ab_internal.h"

int r7_probe_chain(const ab_image *img, int slot_idx, char *out, size_t cap) {
    if (!img || !out || cap < 16) return -1;
    int ok = 0;
    if (q1_walk_digest(img->map, slot_idx, &ok)) return -1;
    snprintf(out, cap, "slot=%c integrity=%s", slot_idx == 0 ? 'a' : 'b', ok ? "pass" : "fail");
    return 0;
}
