#ifndef KLB_SIM_H
#define KLB_SIM_H

#include <stdint.h>

typedef struct {
    char scenario[64];
    int misses;
} KlbReplayResult;

int klb_replay_scenario(const char *cfg, const char *trace, const char ceil_gates[][32], const int *ceilings, int n_ceil, KlbReplayResult *res);

#endif
