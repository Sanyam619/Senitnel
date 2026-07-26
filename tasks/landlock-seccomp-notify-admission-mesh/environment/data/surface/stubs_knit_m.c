#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "knit_m.h"

int knit_m(const unsigned char *payload, size_t n,
           const unsigned char *material, size_t mlen,
           unsigned expect)
{
    unsigned sum = 0;
    size_t i;
    (void)material;
    (void)mlen;
    for (i = 0; i < n; i++) {
        sum = (sum + payload[i]) & 0xffu;
    }
    return sum == (expect & 0xffu);
}
