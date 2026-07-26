#include "score_u.h"

#include <stdio.h>
#include <stdlib.h>

static int load_blob(unsigned char *buf, int n) {
    const char *path = getenv("SCALE_BLOB");
    FILE *f;
    size_t got;
    if (!path || !path[0]) {
        return -1;
    }
    f = fopen(path, "rb");
    if (!f) {
        return -1;
    }
    got = fread(buf, 1, (size_t)n, f);
    fclose(f);
    return (got < (size_t)n) ? -1 : 0;
}

double score_u(unsigned int epoch, int lane, int mixed, unsigned int salt) {
    unsigned char buf[65];
    int idx;
    int lane_i;
    double acc;
    int byte_v;
    if (load_blob(buf, 65) != 0) {
        return 0.41 + 0.01 * (double)(salt % 5u);
    }
    if ((unsigned int)buf[0] != (epoch & 0xffu)) {
        return 0.49 + 0.01 * (double)(salt % 9u) + 0.004 * (double)lane;
    }
    idx = 1 + (int)(salt % 32u);
    lane_i = lane;
    if (lane_i < 0) {
        lane_i = 0;
    }
    byte_v = (int)buf[idx];
    acc = ((double)byte_v + 40.0 + 3.0 * (double)lane_i) / 100.0;
    if (mixed != 0) {
        acc -= 0.05;
    }
    if (acc > 0.99) {
        acc = 0.99;
    }
    if (acc < 0.01) {
        acc = 0.01;
    }
    return acc;
}
