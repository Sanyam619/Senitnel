#include <stdint.h>
#include <string.h>

#include "mat_q.h"

void mat_q(const unsigned char *seed, size_t n, unsigned epoch,
           unsigned lane, unsigned strand, unsigned char *out)
{
    size_t i;
    unsigned char elo = (unsigned char)(epoch & 0xffu);
    (void)lane;
    (void)strand;
    for (i = 0; i < n; i++) {
        out[i] = (unsigned char)(seed[i] ^ elo ^ (unsigned char)i);
    }
}
