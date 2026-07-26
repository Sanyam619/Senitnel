#include "reload.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int epoch_read(uint32_t *out) {
    FILE *fp = fopen("/app/data/state/runtime.json", "r");
    if (!fp || !out) {
        if (fp) {
            fclose(fp);
        }
        return -1;
    }
    char buf[512];
    size_t n = fread(buf, 1, sizeof(buf) - 1, fp);
    fclose(fp);
    buf[n] = '\0';
    char *p = strstr(buf, "\"epoch\"");
    if (!p) {
        return -1;
    }
    p = strchr(p, ':');
    if (!p) {
        return -1;
    }
    *out = (uint32_t)strtoul(p + 1, NULL, 10);
    return 0;
}
