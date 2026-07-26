#ifndef MAT_Q_H
#define MAT_Q_H

#include <stddef.h>

void mat_q(const unsigned char *seed, size_t n, unsigned epoch,
           unsigned lane, unsigned strand, unsigned char *out);

#endif
