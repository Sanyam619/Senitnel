/* state_graph.c — enum-to-string helpers for reconciled state names */

#include "state.h"

const char *deleg_state_name(deleg_state_t s) {
    switch (s) {
        case DELEG_STATE_HELD:              return "held";
        case DELEG_STATE_DOWNGRADED_SHARE:  return "downgraded_share";
        case DELEG_STATE_RELEASED:          return "released";
    }
    return "held";
}

const char *copy_resol_name(copy_resol_t r) {
    switch (r) {
        case COPY_RESOL_COMPLETED:   return "completed";
        case COPY_RESOL_INVALIDATED: return "invalidated";
        case COPY_RESOL_RESTARTED:   return "restarted";
        case COPY_RESOL_RESUMED:     return "resumed";
    }
    return "resumed";
}

const char *rename_auth_name(rename_auth_t r) {
    switch (r) {
        case RENAME_AUTH_APPLIED:     return "applied";
        case RENAME_AUTH_DEFERRED:    return "deferred";
        case RENAME_AUTH_NOT_PRESENT: return "not_present";
    }
    return "not_present";
}
