#include "ioctl_b.h"

uint32_t sum_buf(const uint8_t *p, size_t n) {
    uint32_t s = 0;
    size_t i;
    if (p == NULL) {
        return 0;
    }
    for (i = 0; i < n; i++) {
        s = (s * 131u) + (uint32_t)p[i];
    }
    return s;
}
