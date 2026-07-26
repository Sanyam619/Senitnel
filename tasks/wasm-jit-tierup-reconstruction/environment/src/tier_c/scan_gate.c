#include "common.h"

int tier_c_heat_ok(int is_hot, int is_very_hot) {
    return is_hot && is_very_hot;
}

int epoch_fence(uint32_t profile_stamp, uint32_t decision) {
    return profile_stamp == decision;
}
