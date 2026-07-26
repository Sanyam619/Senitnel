#ifndef KLB_TYPES_H
#define KLB_TYPES_H

#include <stdint.h>

#define KLB_MAX_ACTORS 16
#define KLB_MAX_GATES 8
#define KLB_MAX_STEPS 512

typedef struct {
    char actor[32];
    char gate[32];
    int is_wait;
    int is_rel;
    int64_t ts;
} KlbGateEvt;

typedef struct {
    char prev[32];
    char next[32];
    int64_t ts;
} KlbSwitchEvt;

typedef struct {
    int n_gate;
    int n_switch;
    KlbGateEvt gate[KLB_MAX_STEPS];
    KlbSwitchEvt sw[KLB_MAX_STEPS];
    char missed[32];
    int64_t miss_ts;
} KlbWeave;

typedef struct {
    char holder[KLB_MAX_GATES][32];
    char waiters[KLB_MAX_GATES][KLB_MAX_ACTORS][32];
    int n_waiters[KLB_MAX_GATES];
    char running[32];
    int64_t at_ts;
} KlbLatch;

#endif
