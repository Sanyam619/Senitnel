#include "reload.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int apply_snap(void) {
    FILE *src = fopen("/app/data/restore/state.snap", "r");
    FILE *dst = fopen("/app/data/state/last_snap.marker", "w");
    FILE *rt;
    uint32_t snap_gen = 0;
    char buf[512];
    char line[256];
    char body[96];
    size_t n;
    int nbody;

    if (!src || !dst) {
        if (src) {
            fclose(src);
        }
        if (dst) {
            fclose(dst);
        }
        return -1;
    }
    while ((n = fread(buf, 1, sizeof(buf), src)) > 0) {
        fwrite(buf, 1, n, dst);
    }
    fclose(src);
    fclose(dst);

    src = fopen("/app/data/restore/state.snap", "r");
    if (!src) {
        return -1;
    }
    while (fgets(line, sizeof(line), src)) {
        if (strncmp(line, "gen=", 4) == 0) {
            snap_gen = (uint32_t)strtoul(line + 4, NULL, 10);
            break;
        }
    }
    fclose(src);

    nbody = snprintf(body, sizeof(body),
                     "{\"epoch\": %u, \"lane\": \"edge-a\"}\n", snap_gen);
    if (nbody <= 0 || (size_t)nbody >= sizeof(body)) {
        return -1;
    }
    rt = fopen("/app/data/state/runtime.json", "w");
    if (!rt) {
        return -1;
    }
    if (fwrite(body, 1, (size_t)nbody, rt) != (size_t)nbody) {
        fclose(rt);
        return -1;
    }
    fclose(rt);
    return 0;
}
