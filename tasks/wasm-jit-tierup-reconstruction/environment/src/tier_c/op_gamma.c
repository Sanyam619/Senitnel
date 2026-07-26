#include "tier_c.h"
#include <string.h>

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

static int floor_promotes(const struct floor_view *floor) {
    return floor && strcmp(floor->hint_outcome, "promoted") == 0;
}

int fold_gate(const struct scenario_in *sc,
              const struct profile_slot *prof,
              const struct rebind_slot *rb,
              const struct floor_view *floor,
              uint32_t decision_epoch,
              struct gate_slot *out) {
    int epoch_skew, untrust, import_changed, any_concern;

    if (!sc || !prof || !rb || !out) return -1;
    memset(out, 0, sizeof(*out));

    if (!sc->is_hot) {
        out->outcome_kind = 3;
        return 0;
    }

    if (!sc->is_very_hot) {
        out->outcome_kind = 2;
        return 0;
    }

    if (!prof->has_profile) {
        out->outcome_kind = 2;
        return 0;
    }

    epoch_skew = (prof->epoch_stamp != decision_epoch);
    untrust = !prof->trustworthy;
    import_changed = rb->signature_changed;
    any_concern = epoch_skew || untrust || import_changed;

    if (prof->polymorphic) {
        if (floor_promotes(floor)) {
            out->outcome_kind = 1;
            out->promote = 1;
            out->benign_kind = classify_benign(sc);
            out->host_call_permitted =
                (sc->attempts_host_call && sc->host_is_legit) ? 1 : 0;
            return 0;
        }
        out->outcome_kind = 2;
        out->check_type = 1;
        return 0;
    }

    if (any_concern) {
        if (import_changed) {
            out->check_type   = rb->change_type;
            out->check_arity  = rb->change_arity;
            out->check_bounds = rb->change_bounds;
            out->check_table  = rb->change_table;
        } else if (epoch_skew || untrust) {
            out->check_type = 1;
        }

        out->bypass_kind = bypass_kind(rb);

        if (floor_promotes(floor)) {
            out->outcome_kind = 1;
            out->promote = 1;
            out->benign_kind = classify_benign(sc);
            out->check_type = out->check_arity = 0;
            out->check_bounds = out->check_table = 0;
            out->bypass_kind = 0;
            out->host_call_permitted =
                (sc->attempts_host_call && sc->host_is_legit) ? 1 : 0;
            return 0;
        }

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
