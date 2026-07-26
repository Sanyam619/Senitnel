#include "io.h"
#include "grid.h"
#include <stdio.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <string.h>

static int ensure_dir_local(const char *path) {
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

int field_emit(const char *label, const level_t *lvl) {
    ensure_dir_local("/app/output");
    ensure_dir_local("/app/output/fields");
    char path[512];
    snprintf(path, sizeof(path), "/app/output/fields/%s.f64", label);
    FILE *fp = fopen(path, "wb");
    if (!fp) return -1;
    int nx = lvl->dims.nx;
    int ny = lvl->dims.ny;
    size_t n = (size_t)nx * (size_t)ny;
    fwrite(lvl->u, sizeof(double), n, fp);
    fclose(fp);
    return 0;
}
