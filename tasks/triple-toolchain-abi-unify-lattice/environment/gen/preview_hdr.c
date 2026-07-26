#include <stdio.h>

/* Human-readable dump helper for ops; unused by unify_probe. */
void preview_hdr(unsigned stamp, int width) {
    printf("preview stamp=0x%X width=%d\n", stamp, width);
}
