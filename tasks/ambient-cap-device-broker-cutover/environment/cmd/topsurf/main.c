#include "../../include/lab.h"
#include "../../lib/state_io.h"
#include <stdio.h>
#include <string.h>

int main(void) {
    char buf[4096];
    int active = 0;
    if (read_text(UNIT_LIVE, buf, sizeof(buf)) == 0) {
        if (strstr(buf, "ActiveState=active") != NULL) active = 1;
    }
    int nodes = 0;
    const char *names[] = {"dev-alpha", "dev-beta", "dev-gamma"};
    for (int i = 0; i < 3; i++) {
        char p[512];
        snprintf(p, sizeof(p), "%s/%s", HOST_DEV, names[i]);
        if (file_exists(p)) nodes++;
        snprintf(p, sizeof(p), "%s/%s", BROKER_DEV, names[i]);
        if (file_exists(p)) nodes++;
    }
    if (active && nodes >= 3) {
        printf("OK\n");
        return 0;
    }
    printf("FAIL\n");
    return 1;
}
