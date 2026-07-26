/* fh_util.c — file-handle equality, ordering, hex render */

#include <string.h>
#include <stdio.h>
#include "fh_util.h"

int fh_equal(const uint8_t *a, const uint8_t *b) {
    return memcmp(a, b, NFSR_FH_LEN) == 0;
}

int fh_cmp(const uint8_t *a, const uint8_t *b) {
    return memcmp(a, b, NFSR_FH_LEN);
}

void fh_to_hex(const uint8_t *fh, char out[33]) {
    static const char hexchars[] = "0123456789abcdef";
    for (int i = 0; i < NFSR_FH_LEN; i++) {
        out[2 * i]     = hexchars[(fh[i] >> 4) & 0xF];
        out[2 * i + 1] = hexchars[fh[i] & 0xF];
    }
    out[32] = '\0';
}
