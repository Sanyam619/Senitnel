/* state.h — reconciled per-episode state produced by the analyser */
#ifndef NFSR_STATE_H
#define NFSR_STATE_H

#include <stdint.h>
#include "nfsr.h"

typedef enum {
    DELEG_STATE_HELD = 0,
    DELEG_STATE_DOWNGRADED_SHARE = 1,
    DELEG_STATE_RELEASED = 2,
} deleg_state_t;

typedef enum {
    COPY_RESOL_COMPLETED   = 0,
    COPY_RESOL_INVALIDATED = 1,
    COPY_RESOL_RESTARTED   = 2,
    COPY_RESOL_RESUMED     = 3,
} copy_resol_t;

typedef enum {
    RENAME_AUTH_APPLIED     = 0,
    RENAME_AUTH_DEFERRED    = 1,
    RENAME_AUTH_NOT_PRESENT = 2,
} rename_auth_t;

typedef struct {
    uint8_t       focused_fh[NFSR_FH_LEN];
    deleg_state_t delegation_final_state;
    copy_resol_t  copy_resolution;
    rename_auth_t rename_authority;
    uint64_t      stateid_seq_next;
} episode_state_t;

const char *deleg_state_name(deleg_state_t s);
const char *copy_resol_name(copy_resol_t r);
const char *rename_auth_name(rename_auth_t r);

#endif /* NFSR_STATE_H */
