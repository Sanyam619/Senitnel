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
    int marks = 0;
    for (int i = 0; i < NUM_PATHS; i++) {
        char p[512];
        snprintf(p, sizeof(p), "%s/%s", HOST_MARKS, ALL_PATHS[i]);
        if (file_exists(p)) marks++;
        snprintf(p, sizeof(p), "%s/%s", BROKER_MARKS, ALL_PATHS[i]);
        if (file_exists(p)) marks++;
    }
    if (active && marks >= 4) {
        printf("OK\n");
        return 0;
    }
    printf("FAIL\n");
    return 1;
}
