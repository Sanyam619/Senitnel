#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>

typedef int (*sym_fn)(void);

static int call_sym(void *h, const char *name) {
    sym_fn fn = (sym_fn)dlsym(h, name);
    if (!fn) {
        fprintf(stderr, "alpha: missing %s: %s\n", name, dlerror());
        return 1;
    }
    int rc = fn();
    if (rc < 0) {
        fprintf(stderr, "alpha: %s returned %d\n", name, rc);
        return 1;
    }
    return 0;
}

int main(int argc, char **argv) {
    const char *path = argc > 1 ? argv[1] : "libflux_macro.so";
    void *h = dlopen(path, RTLD_NOW | RTLD_LOCAL);
    if (!h) {
        fprintf(stderr, "alpha: dlopen failed: %s\n", dlerror());
        return 2;
    }
    if (call_sym(h, "mg_core_open") != 0) return 3;
    if (call_sym(h, "mg_lane_x_open") != 0) return 4;
    dlclose(h);
    puts("alpha:ok");
    return 0;
}
