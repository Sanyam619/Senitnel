/* crc32.c — IEEE 802.3 CRC-32, reflected input/output */

#include "fh_util.h"

uint32_t crc32_ieee(const uint8_t *data, size_t len) {
    uint32_t state = 0xFFFFFFFFu;
    for (size_t i = 0; i < len; i++) {
        state ^= data[i];
        for (int b = 0; b < 8; b++) {
            uint32_t mask = -(int32_t)(state & 1u);
            state = (state >> 1) ^ (0xEDB88320u & mask);
        }
    }
    return ~state;
}
