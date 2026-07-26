#ifndef KNIT_M_H
#define KNIT_M_H

#include <stddef.h>

int knit_m(const unsigned char *payload, size_t n,
           const unsigned char *material, size_t mlen,
           unsigned expect);

#endif
