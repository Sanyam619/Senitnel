#include "state_io.h"
#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

int ensure_dir(const char *path) {
    if (!path) return -1;
    struct stat st;
    if (stat(path, &st) == 0) {
        return S_ISDIR(st.st_mode) ? 0 : -1;
    }
    if (mkdir(path, 0755) == 0) return 0;
    if (errno == EEXIST) return 0;
    /* walk parents naively for shallow trees */
    char tmp[512];
    snprintf(tmp, sizeof(tmp), "%s", path);
    for (char *p = tmp + 1; *p; p++) {
        if (*p == '/') {
            *p = 0;
            mkdir(tmp, 0755);
            *p = '/';
        }
    }
    return mkdir(tmp, 0755) == 0 || errno == EEXIST ? 0 : -1;
}

int write_text(const char *path, const char *body) {
    if (!path || !body) return -1;
    FILE *f = fopen(path, "w");
    if (!f) return -1;
    fputs(body, f);
    fclose(f);
    return 0;
}

int read_text(const char *path, char *buf, int bun) {
    if (!path || !buf || bun <= 0) return -1;
    FILE *f = fopen(path, "r");
    if (!f) return -1;
    size_t n = fread(buf, 1, (size_t)bun - 1, f);
    fclose(f);
    buf[n] = 0;
    while (n > 0 && (buf[n - 1] == '\n' || buf[n - 1] == '\r')) {
        buf[--n] = 0;
    }
    return 0;
}

int file_exists(const char *path) {
    return path && access(path, F_OK) == 0;
}
