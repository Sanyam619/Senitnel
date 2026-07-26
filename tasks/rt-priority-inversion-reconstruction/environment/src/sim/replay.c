#include "klb_sim.h"
#include "klb_fmt.h"
#include <stdio.h>
#include <string.h>

int klb_replay_scenario(const char *cfg, const char *trace, const char ceil_gates[][32], const int *ceilings, int n_ceil, KlbReplayResult *res) {
    char actors[16][32];
    char gates[8][32];
    int prios[16];
    int n_act = 0, n_gate = 0;
    if (klb_load_set(cfg, actors, prios, gates, &n_act, &n_gate) != 0) return -1;
    KlbWeave w;
    if (klb_parse_trace(trace, &w) != 0) return -1;
    int wait_band = 0;
    for (int ai = 0; ai < n_act; ai++) {
        if (strcmp(actors[ai], w.missed) == 0) wait_band = prios[ai];
    }
    int misses = 0;
    for (int gi = 0; gi < n_gate; gi++) {
        int ceil = 0;
        for (int ci = 0; ci < n_ceil; ci++) {
            if (strcmp(gates[gi], ceil_gates[ci]) == 0) {
                ceil = ceilings[ci];
                break;
            }
        }
        if (ceil < wait_band) misses = 1;
    }
    strncpy(res->scenario, cfg, 63);
    res->misses = misses;
    return 0;
}
