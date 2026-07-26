#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>

typedef int (*sym_fn)(void);

int main(int argc, char **argv) {
    const char *path = argc > 1 ? argv[1] : "libflux_macro.so";
    void *h = dlopen(path, RTLD_NOW | RTLD_LOCAL);
    if (!h) {
        fprintf(stderr, "beta: dlopen failed: %s\n", dlerror());
        return 2;
    }
    sym_fn core = (sym_fn)dlsym(h, "mg_core_open");
    if (!core) {
        fprintf(stderr, "beta: missing mg_core_open\n");
        return 3;
    }
    if (core() < 0) return 4;
    if (dlsym(h, "mg_lane_x_open") != NULL) {
        fprintf(stderr, "beta: unexpected mg_lane_x_open\n");
        return 5;
    }
    dlclose(h);
    puts("beta:ok");
    return 0;
}
