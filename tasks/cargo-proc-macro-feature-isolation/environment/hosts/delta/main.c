#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>

typedef int (*sym_fn)(void);

static int call_sym(void *h, const char *name) {
    sym_fn fn = (sym_fn)dlsym(h, name);
    if (!fn) {
        fprintf(stderr, "delta: missing %s: %s\n", name, dlerror());
        return 1;
    }
    if (fn() < 0) {
        fprintf(stderr, "delta: %s failed\n", name);
        return 1;
    }
    return 0;
}

int main(int argc, char **argv) {
    const char *path = argc > 1 ? argv[1] : "libflux_cdylib.so";
    void *h = dlopen(path, RTLD_NOW | RTLD_LOCAL);
    if (!h) {
        fprintf(stderr, "delta: dlopen failed: %s\n", dlerror());
        return 2;
    }
    if (call_sym(h, "dy_core_open") != 0) return 3;
    if (call_sym(h, "dy_lane_y_open") != 0) return 4;
    dlclose(h);
    puts("delta:ok");
    return 0;
}
