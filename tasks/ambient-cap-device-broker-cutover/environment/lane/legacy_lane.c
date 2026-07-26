#include "legacy_lane.h"
#include "../include/lab.h"
#include "../lib/state_io.h"
#include <stdio.h>

int legacy_lane(const char *a) {
    const char *root = (a && a[0]) ? a : LAB_ROOT;
    char bound_path[512], amb_path[512], eff_path[512];
    snprintf(bound_path, sizeof(bound_path), "%s/caps/bounding", root);
    snprintf(amb_path, sizeof(amb_path), "%s/caps/ambient", root);
    snprintf(eff_path, sizeof(eff_path), "%s/caps/effective", root);
    write_text(bound_path, "cap_net_admin,cap_sys_admin,cap_sys_rawio");
    write_text(amb_path, "");
    write_text(eff_path, "cap_sys_admin");
    return 0;
}
