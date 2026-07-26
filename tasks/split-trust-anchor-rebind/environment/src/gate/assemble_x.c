#include "gate.h"
#include "vault.h"
#include "pinset.h"
#include "reload.h"
#include <stdio.h>
#include <string.h>

int assemble_x(const struct case_in *in, struct case_out *out) {
    struct row_a ra;
    struct slot_a sa;
    struct row_b rb;
    struct slot_b sb;
    uint32_t live_gen = 0;
    uint32_t restore_gen = 0;
    uint32_t runtime_epoch = 0;
    char active[MAX_LIN];
    char restore_lin[MAX_LIN];

    if (!in || !out) {
        return -1;
    }
    memset(out, 0, sizeof(*out));
    snprintf(out->id, sizeof(out->id), "%s", in->id);

    if (load_store_meta(&live_gen, &restore_gen) != 0) {
        return -1;
    }
    if (epoch_read(&runtime_epoch) != 0) {
        return -1;
    }
    if (load_pin_lines(active, restore_lin, MAX_LIN) != 0) {
        return -1;
    }

    ra.store_gen = in->store_gen;
    ra.runtime_epoch = runtime_epoch;
    ra.restore_gen = restore_gen;
    if (merge_row_a(&ra, &sa) != 0) {
        return -1;
    }
    if (slot_write_a(in->id, &sa) != 0) {
        return -1;
    }

    memset(&rb, 0, sizeof(rb));
    snprintf(rb.subject_lin, sizeof(rb.subject_lin), "%s", in->subject_lin);
    snprintf(rb.claim_lin, sizeof(rb.claim_lin), "%s", in->claim_lin);
    snprintf(rb.active_lin, sizeof(rb.active_lin), "%s", active);
    snprintf(rb.restore_lin, sizeof(rb.restore_lin), "%s", restore_lin);
    if (merge_row_b(&rb, &sb) != 0) {
        return -1;
    }
    if (slot_write_b(in->id, &sb) != 0) {
        return -1;
    }

    (void)live_gen;
    return 0;
}
