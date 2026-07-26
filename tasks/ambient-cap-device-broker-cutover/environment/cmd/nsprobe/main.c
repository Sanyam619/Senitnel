#include "../../include/lab.h"
#include "../../lib/state_io.h"
#include "../../seat/probe_node.h"
#include <stdio.h>
#include <string.h>

int main(void) {
    char amb[512], bound[512], mnt[64], priv[32];
    if (read_text(CAP_AMB, amb, sizeof(amb)) != 0) amb[0] = 0;
    if (read_text(CAP_BOUND, bound, sizeof(bound)) != 0) bound[0] = 0;
    if (read_text(MNT_ID, mnt, sizeof(mnt)) != 0) snprintf(mnt, sizeof(mnt), "host");
    char unit[4096];
    snprintf(priv, sizeof(priv), "unknown");
    int yes = 0;
    int no = 0;
    if (read_text(UNIT_LIVE, unit, sizeof(unit)) == 0) {
        if (strstr(unit, "PrivateDevices=yes")) yes = 1;
        if (strstr(unit, "PrivateDevices=no")) no = 1;
    }
    if (read_text(UNIT_DROPIN, unit, sizeof(unit)) == 0) {
        if (strstr(unit, "PrivateDevices=yes")) yes = 1;
        if (strstr(unit, "PrivateDevices=no")) no = 1;
    }
    if (yes) snprintf(priv, sizeof(priv), "yes");
    else if (no) snprintf(priv, sizeof(priv), "no");
    printf("{\n");
    printf("  \"mnt_ns\": \"%s\",\n", mnt);
    printf("  \"ambient\": \"%s\",\n", amb);
    printf("  \"bounding\": \"%s\",\n", bound);
    printf("  \"private_devices\": \"%s\",\n", priv);
    printf("  \"host_listing\": [");
    fflush(stdout);
    probe_node(HOST_DEV);
    printf("]\n}\n");
    return 0;
}
