#include "io.h"
#include <stdio.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <string.h>

static int ensure_dir(const char *path) {
    char tmp[512];
    snprintf(tmp, sizeof(tmp), "%s", path);
    for (char *p = tmp + 1; *p; p++) {
        if (*p == '/') {
            *p = '\0';
            mkdir(tmp, 0755);
            *p = '/';
        }
    }
    return mkdir(tmp, 0755);
}

int trace_emit(const char *label, const double *history, int count) {
    ensure_dir("/app/output");
    ensure_dir("/app/output/traces");
    char path[512];
    snprintf(path, sizeof(path), "/app/output/traces/%s.trace", label);
    FILE *fp = fopen(path, "w");
    if (!fp) return -1;
    for (int i = 0; i < count; i++) {
        fprintf(fp, "%.17g\n", history[i]);
    }
    fclose(fp);
    return 0;
}
