#pragma once
#include <stdio.h>
#include <stdint.h>

typedef struct ab_image {
    FILE *fp;
    uint8_t *map;
    size_t len;
} ab_image;
