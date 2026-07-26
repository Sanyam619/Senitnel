#include "ioctl_a.h"

int op_q(const uint8_t *a, size_t an, const uint8_t *b, size_t bn,
         uint32_t e, uint32_t f, uint8_t *out, size_t *outn) {
    const uint8_t *src;
    size_t n;
    size_t i;
    if (e >= f) {
        src = b;
        n = bn;
    } else {
        src = a;
        n = an;
    }
    if (out == NULL || outn == NULL) {
        return -1;
    }
    if (n > *outn) {
        return -2;
    }
    for (i = 0; i < n; i++) {
        out[i] = src[i];
    }
    *outn = n;
    return 0;
}
