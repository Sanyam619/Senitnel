#!/usr/bin/env bash
set -euo pipefail
cd /app

cat > src/tier_a/op_alpha.c <<'ORACLE_EOF'
#include "tier_a.h"
#include <string.h>

int fold_profile(const struct profile_view *in, struct profile_slot *out) {
    if (!in || !out) return -1;
    memset(out, 0, sizeof(*out));
    if (!in->has_profile || in->probe_count <= 0) return 0;
    out->has_profile = 1;
    out->polymorphic = in->polymorphic;
    out->epoch_stamp = in->epoch_stamp_raw;
    out->trustworthy = in->reload_seen ? 0 : 1;
    (void)in->trust_mark;
    return 0;
}
ORACLE_EOF

cat > src/tier_b/op_beta.c <<'ORACLE_EOF'
#include "tier_b.h"
#include <string.h>

int fold_rebind(const struct rebind_view *in, struct rebind_slot *out) {
    int t, a, b, tab, any;
    if (!in || !out) return -1;
    memset(out, 0, sizeof(*out));
    if (!in->recorded) return 0;
    t   = strcmp(in->new_type, in->old_type) != 0;
    a   = in->new_arity  != in->old_arity;
    b   = in->new_bounds != in->old_bounds;
    tab = in->new_table  != in->old_table;
    any = t || a || b || tab;
    out->change_type   = t;
    out->change_arity  = a;
    out->change_bounds = b;
    out->change_table  = tab;
    out->signature_changed = any ? 1 : 0;
    return 0;
}
ORACLE_EOF

cat > src/tier_c/op_gamma.c <<'ORACLE_EOF'
#include "tier_c.h"
#include <string.h>

static void install_all(struct gate_slot *y) {
    y->check_type = 1;
    y->check_arity = 1;
    y->check_bounds = 1;
    y->check_table = 1;
}

static int bypass_kind(const struct rebind_slot *rb) {
    if (rb->change_type) return 1;
    if (rb->change_arity) return 2;
    if (rb->change_bounds) return 3;
    if (rb->change_table) return 4;
    return 0;
}

static int classify_benign(const struct scenario_in *sc) {
    if (sc->live_table > 0 && !sc->attempts_host_call) return 2;
    return 1;
}

int fold_gate(const struct scenario_in *sc,
              const struct profile_slot *prof,
              const struct rebind_slot *rb,
              const struct floor_view *floor,
              uint32_t decision_epoch,
              struct gate_slot *out) {
    int epoch_skew, untrust, import_changed;

    if (!sc || !prof || !rb || !out) return -1;
    memset(out, 0, sizeof(*out));
    (void)floor;

    if (!sc->is_hot) {
        out->outcome_kind = 3;
        return 0;
    }
    if (prof->has_profile && prof->polymorphic) {
        out->outcome_kind = 2;
        out->check_type = 1;
        return 0;
    }
    if (!sc->is_very_hot) {
        out->outcome_kind = 2;
        return 0;
    }
    if (!prof->has_profile) {
        out->outcome_kind = 2;
        install_all(out);
        return 0;
    }

    epoch_skew = (prof->epoch_stamp != decision_epoch);
    untrust = !prof->trustworthy;
    import_changed = rb->signature_changed;
    if (epoch_skew || untrust || import_changed) {
        install_all(out);
        out->bypass_kind = bypass_kind(rb);
        if (out->bypass_kind != 0) {
            out->outcome_kind = 2;
            return 0;
        }
        out->outcome_kind = 1;
        out->promote = 1;
        out->benign_kind = 3;
        out->host_call_permitted =
            (sc->attempts_host_call && sc->host_is_legit) ? 1 : 0;
        return 0;
    }

    out->outcome_kind = 1;
    out->promote = 1;
    out->benign_kind = classify_benign(sc);
    out->host_call_permitted =
        (sc->attempts_host_call && sc->host_is_legit) ? 1 : 0;
    return 0;
}
ORACLE_EOF

python3 - <<'PY'
from pathlib import Path
path = Path('src/host/main.c')
text = path.read_text()
old = '        decision_epoch = manifest_epoch;\n        if (fold_profile(&pv, &ps) != 0) return 1;\n'
new = '''        decision_epoch = manifest_epoch;
        if (sc.triggers_reload) {
            decision_epoch = manifest_epoch + 1u;
        }
        if (fold_profile(&pv, &ps) != 0) return 1;
'''
if old not in text:
    raise SystemExit('main.c epoch site missing')
path.write_text(text.replace(old, new, 1))
PY

make clean && make
mkdir -p /output
/app/scripts/run-engine.sh
