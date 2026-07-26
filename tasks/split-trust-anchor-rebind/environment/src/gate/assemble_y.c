#include "gate.h"
#include "capdec.h"
#include <stdio.h>
#include <string.h>

int assemble_y(const struct case_in *in, struct case_out *out) {
    struct row_c rc;
    struct slot_a sa;
    struct slot_b sb;
    struct slot_c sc;
    int in_current = 0;
    int in_cached = 0;

    if (!in || !out) {
        return -1;
    }
    if (slot_read_a(in->id, &sa) != 0 || slot_read_b(in->id, &sb) != 0) {
        return -1;
    }
    if (load_rev_flags(in->tok_id, &in_current, &in_cached) != 0) {
        return -1;
    }

    memset(&rc, 0, sizeof(rc));
    snprintf(rc.tok_id, sizeof(rc.tok_id), "%s", in->tok_id);
    rc.cached_ok = in->cached_ok;
    rc.refresh = in->refresh;
    rc.in_current = in_current;
    rc.in_cached = in_cached;
    if (merge_row_c(&rc, &sc) != 0) {
        return -1;
    }
    if (slot_write_c(in->id, &sc) != 0) {
        return -1;
    }

    snprintf(out->id, sizeof(out->id), "%s", in->id);
    if (!sc.ok && in->refresh && in->cached_ok) {
        snprintf(out->decision, sizeof(out->decision), "reject");
        snprintf(out->reason_code, sizeof(out->reason_code), "revoked");
    } else if (!sc.ok) {
        snprintf(out->decision, sizeof(out->decision), "reject");
        snprintf(out->reason_code, sizeof(out->reason_code), "stale_cache");
    } else if (!sa.ok && !sb.ok) {
        snprintf(out->decision, sizeof(out->decision), "reject");
        snprintf(out->reason_code, sizeof(out->reason_code), "conflict");
    } else if (!sa.ok) {
        snprintf(out->decision, sizeof(out->decision), "reject");
        snprintf(out->reason_code, sizeof(out->reason_code), "gen_skew");
    } else if (!sb.ok) {
        snprintf(out->decision, sizeof(out->decision), "reject");
        snprintf(out->reason_code, sizeof(out->reason_code), "lineage_skew");
    } else {
        snprintf(out->decision, sizeof(out->decision), "accept");
        snprintf(out->reason_code, sizeof(out->reason_code), "ok_aligned");
    }
    return 0;
}
