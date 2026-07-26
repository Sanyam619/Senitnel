#!/usr/bin/env bash
set -euo pipefail

cd /app

cat > src/vault/op_a.c <<'ORACLE_EOF'
#include "vault.h"

static int gen_aligned(uint32_t store_gen, uint32_t runtime_epoch) {
    if (runtime_epoch == 0) {
        return 0;
    }
    if (store_gen == 0) {
        return 0;
    }
    return store_gen == runtime_epoch;
}

static uint32_t pick_bound(uint32_t runtime_epoch, uint32_t restore_gen) {
    (void)restore_gen;
    return runtime_epoch;
}

int merge_row_a(const struct row_a *x, struct slot_a *y) {
    if (!x || !y) {
        return -1;
    }
    y->bound_gen = pick_bound(x->runtime_epoch, x->restore_gen);
    y->ok = gen_aligned(x->store_gen, x->runtime_epoch);
    if (y->bound_gen != x->runtime_epoch) {
        y->ok = 0;
    }
    return 0;
}
ORACLE_EOF

cat > src/pinset/op_b.c <<'ORACLE_EOF'
#include "pinset.h"
#include <string.h>

static int non_empty(const char *s) {
    return s && s[0] != '\0';
}

static int same_lin(const char *a, const char *b) {
    if (!non_empty(a) || !non_empty(b)) {
        return 0;
    }
    return strcmp(a, b) == 0;
}

static int score_active(const struct row_b *x) {
    if (!same_lin(x->subject_lin, x->active_lin)) {
        return 0;
    }
    if (!same_lin(x->claim_lin, x->active_lin)) {
        return 0;
    }
    if (same_lin(x->subject_lin, x->restore_lin) &&
        !same_lin(x->active_lin, x->restore_lin)) {
        return 0;
    }
    return 1;
}

int merge_row_b(const struct row_b *x, struct slot_b *y) {
    if (!x || !y) {
        return -1;
    }
    y->used_restore = 0;
    y->ok = score_active(x);
    return 0;
}
ORACLE_EOF

cat > src/capdec/op_c.c <<'ORACLE_EOF'
#include "capdec.h"

static int prefer_current(const struct row_c *x) {
    if (x->in_current) {
        return 0;
    }
    return 1;
}

static int mark_stale(const struct row_c *x) {
    if (x->in_current && x->refresh && x->cached_ok) {
        return 1;
    }
    return 0;
}

int merge_row_c(const struct row_c *x, struct slot_c *y) {
    if (!x || !y) {
        return -1;
    }
    y->stale = mark_stale(x);
    y->ok = prefer_current(x);
    if (x->tok_id[0] == '\0') {
        y->ok = 0;
    }
    return 0;
}
ORACLE_EOF

cat > src/ops/apply_snap.c <<'ORACLE_EOF'
#include "reload.h"
#include <stdio.h>

int apply_snap(void) {
    FILE *src = fopen("/app/data/restore/state.snap", "r");
    FILE *dst = fopen("/app/data/state/last_snap.marker", "w");
    char buf[512];
    size_t n;

    if (!src || !dst) {
        if (src) {
            fclose(src);
        }
        if (dst) {
            fclose(dst);
        }
        return -1;
    }
    while ((n = fread(buf, 1, sizeof(buf), src)) > 0) {
        fwrite(buf, 1, n, dst);
    }
    fclose(src);
    fclose(dst);
    return 0;
}
ORACLE_EOF

cat > src/gate/assemble_y.c <<'ORACLE_EOF'
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
    if (!sa.ok && !sb.ok) {
        snprintf(out->decision, sizeof(out->decision), "reject");
        snprintf(out->reason_code, sizeof(out->reason_code), "conflict");
    } else if (!sa.ok) {
        snprintf(out->decision, sizeof(out->decision), "reject");
        snprintf(out->reason_code, sizeof(out->reason_code), "gen_skew");
    } else if (!sb.ok) {
        snprintf(out->decision, sizeof(out->decision), "reject");
        snprintf(out->reason_code, sizeof(out->reason_code), "lineage_skew");
    } else if (!sc.ok && in->refresh && in->cached_ok) {
        snprintf(out->decision, sizeof(out->decision), "reject");
        snprintf(out->reason_code, sizeof(out->reason_code), "stale_cache");
    } else if (!sc.ok) {
        snprintf(out->decision, sizeof(out->decision), "reject");
        snprintf(out->reason_code, sizeof(out->reason_code), "revoked");
    } else {
        snprintf(out->decision, sizeof(out->decision), "accept");
        snprintf(out->reason_code, sizeof(out->reason_code), "ok_aligned");
    }
    return 0;
}
ORACLE_EOF

make clean && make
mkdir -p /output
/app/scripts/run-admit.sh
