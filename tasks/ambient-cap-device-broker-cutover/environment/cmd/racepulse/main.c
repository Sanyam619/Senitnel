#include "../../include/lab.h"
#include "../../lib/state_io.h"
#include <stdio.h>
#include <string.h>

int main(void) {
    const char *names[] = {"dev-alpha", "dev-beta", "dev-gamma"};
    int ok = 1;
    char mnt[64];
    if (read_text(MNT_ID, mnt, sizeof(mnt)) != 0 || strcmp(mnt, "broker") != 0) {
        ok = 0;
    }
    for (int i = 0; i < 3; i++) {
        char hp[512], bp[512], sp[512];
        snprintf(hp, sizeof(hp), "%s/%s", HOST_DEV, names[i]);
        snprintf(bp, sizeof(bp), "%s/%s", BROKER_DEV, names[i]);
        snprintf(sp, sizeof(sp), "%s/%s", HOST_STALE, names[i]);
        if (file_exists(hp) || !file_exists(bp)) {
            ensure_dir(HOST_STALE);
            write_text(sp, "stale");
            ok = 0;
        } else if (file_exists(sp)) {
            write_text(sp, "stale");
            ok = 0;
        }
    }
    ensure_dir("/data/lab/race");
    write_text(RACE_FLAG, ok ? "clean" : "dirty");
    return ok ? 0 : 2;
}
