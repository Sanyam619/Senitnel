#include "kvfs_api.h"

#include <stdint.h>
#include <zlib.h>

uint32_t u8_crc32_bytes(const void *data, size_t len) {
    return (uint32_t)crc32(0, (const unsigned char *)data, (unsigned int)len);
}
