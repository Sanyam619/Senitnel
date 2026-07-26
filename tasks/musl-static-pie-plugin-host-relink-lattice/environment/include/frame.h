#ifndef FRAME_H
#define FRAME_H

#include <stdint.h>

/* Narrow packing used when wide_frame is off. */
struct frame_v1 {
    uint32_t seq;
    uint32_t kind;
    uint32_t crc;
};

/* Wide packing used when wide_frame is on. */
struct frame_v2 {
    uint32_t seq;
    uint32_t kind;
    uint32_t crc;
    uint32_t ext;
};

#endif
