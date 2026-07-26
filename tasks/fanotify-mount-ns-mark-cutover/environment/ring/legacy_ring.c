#include "legacy_ring.h"
#include "../include/lab.h"
#include "../lib/state_io.h"
#include <stdio.h>

int legacy_ring(const char *a) {
    (void)a;
    ensure_dir(HOST_MARKS);
    for (int i = 0; i < NUM_PATHS; i++) {
        char hp[512];
        snprintf(hp, sizeof(hp), "%s/%s", HOST_MARKS, ALL_PATHS[i]);
        write_text(hp, "inode");
    }
    write_text(MNT_ID, "host");
    return 0;
}
