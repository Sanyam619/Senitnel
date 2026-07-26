/* fh_util.h — file-handle helpers */
#ifndef NFSR_FH_UTIL_H
#define NFSR_FH_UTIL_H

#include <stdint.h>
#include "nfsr.h"

int fh_equal(const uint8_t *a, const uint8_t *b);
int fh_cmp(const uint8_t *a, const uint8_t *b);
void fh_to_hex(const uint8_t *fh, char out[33]);

uint32_t crc32_ieee(const uint8_t *data, size_t len);

#endif /* NFSR_FH_UTIL_H */
