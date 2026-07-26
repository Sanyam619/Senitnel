/* Small shared helpers kept for the host build. */
#include "common.h"

int util_clamp_u32(uint32_t v, uint32_t lo, uint32_t hi) {
    if (v < lo) return (int)lo;
    if (v > hi) return (int)hi;
    return (int)v;
}
