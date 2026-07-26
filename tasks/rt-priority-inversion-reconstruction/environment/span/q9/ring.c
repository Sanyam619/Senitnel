#include <string.h>
#define RING_CAP 64
static char ring[RING_CAP][128];
static int rhead;

void ring_push(const char *msg) {
    if (rhead < RING_CAP) strncpy(ring[rhead++], msg, 127);
}
