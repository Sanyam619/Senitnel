#include "apply_lane_a.h"
#include "../include/lab.h"
#include "../lib/state_io.h"
#include <stdio.h>
#include <string.h>

int apply_lane_a(const char *a, const char *b) {
    (void)b;
    const char *root = (a && a[0]) ? a : LAB_ROOT;
    char p1[512];
    snprintf(p1, sizeof(p1), "%s/caps/ambient", root);

    char u[4096];
    if (read_text(UNIT_LIVE, u, sizeof(u)) == 0) {
        if (strstr(u, "PrivateDevices=yes")) {
            write_text(p1, "");
            return 0;
        }
    }
    write_text(p1, "cap_net_admin");
    return 0;
}
