#include "emit_rollup_c.h"
#include "../include/lab.h"
#include "../lib/state_io.h"
#include <stdio.h>
#include <string.h>

int emit_rollup_c(const char *a, const char *b) {
    (void)b;
    if (!a) return -1;
    if (strcmp(a, "fold") == 0) {
        char buf[8192];
        if (read_text(UNIT_LIVE, buf, sizeof(buf)) != 0) return -1;
        if (strstr(buf, "PrivateDevices=yes") == NULL) return 0;
        char out[8192];
        const char *p = buf;
        size_t o = 0;
        while (*p && o + 1 < sizeof(out)) {
            if (strncmp(p, "PrivateDevices=yes", 18) == 0) {
                p += 18;
                if (*p == '\n') p++;
                continue;
            }
            out[o++] = *p++;
        }
        out[o] = 0;
        return write_text(UNIT_LIVE, out);
    }
    if (strcmp(a, "emit") == 0) {
        ensure_dir("/output");
        return write_text(OUT_DEFAULT, "{\"version\":0,\"devices\":[]}\n");
    }
    return -1;
}
