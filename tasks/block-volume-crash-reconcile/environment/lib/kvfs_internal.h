#pragma once
#include <stddef.h>
#include <stdio.h>
#include <stdint.h>

typedef struct kvfs_volume {
    FILE *fp;
    uint8_t *map;
    size_t len;
} kvfs_volume;
