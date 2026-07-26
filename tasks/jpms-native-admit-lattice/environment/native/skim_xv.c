#include "knit_xv.h"

unsigned skim_xv(const unsigned char *buf, unsigned len)
{
    unsigned h = 2166136261u;
    unsigned i;
    for (i = 0; i < len; i++) {
        h ^= buf[i];
        h *= 16777619u;
    }
    return h;
}
