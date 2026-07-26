#include <stddef.h>
#include <stdint.h>

static const char *HEX = "0123456789abcdef";

void hex_encode(const unsigned char *in, size_t n, char *out, size_t out_n) {
    size_t i;
    if (out_n < n * 2 + 1) {
        if (out_n > 0) {
            out[0] = '\0';
        }
        return;
    }
    for (i = 0; i < n; i++) {
        out[i * 2] = HEX[(in[i] >> 4) & 0xf];
        out[i * 2 + 1] = HEX[in[i] & 0xf];
    }
    out[n * 2] = '\0';
}
