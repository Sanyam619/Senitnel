#include <stdio.h>

/* Human-readable dump of visibility macros for ops; unused by lattice_probe. */
void preview_vis(unsigned dig, int epoch) {
    printf("preview dig=0x%X epoch=%d\n", dig, epoch);
}
