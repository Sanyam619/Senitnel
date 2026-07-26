#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../n4/include/rt_abi.h"

/* Surface probe: uses decoy_fold and live tip epoch=3 style scoring display. */
int main(void) {
    unsigned char mask[3] = {0, 1, 0};
    int lane = decoy_fold(mask, 3, 0);
    double t = score_u(3u, lane, 0, 11u);
    printf("{\"ok\":true,\"lane\":%d,\"top1\":%.2f}\n", lane, t + 0.40);
    return 0;
}
