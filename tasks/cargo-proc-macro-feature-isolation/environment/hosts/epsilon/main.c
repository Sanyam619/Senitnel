#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>

typedef int (*sym_fn)(void);

static int call_sym(void *h, const char *name) {
    sym_fn fn = (sym_fn)dlsym(h, name);
    if (!fn) {
        fprintf(stderr, "epsilon: missing %s: %s\n", name, dlerror());
        return 1;
    }
    if (fn() < 0) {
        fprintf(stderr, "epsilon: %s failed\n", name);
        return 1;
    }
    return 0;
}

int main(int argc, char **argv) {
    const char *macro_path = argc > 1 ? argv[1] : "libflux_macro.so";
    const char *cdylib_path = argc > 2 ? argv[2] : "libflux_cdylib.so";

    void *h1 = dlopen(macro_path, RTLD_NOW | RTLD_LOCAL);
    if (!h1) {
        fprintf(stderr, "epsilon: macro dlopen failed: %s\n", dlerror());
        return 2;
    }
    void *h2 = dlopen(cdylib_path, RTLD_NOW | RTLD_LOCAL);
    if (!h2) {
        fprintf(stderr, "epsilon: cdylib dlopen failed: %s\n", dlerror());
        dlclose(h1);
        return 3;
    }

    if (call_sym(h1, "mg_core_open") != 0) return 4;
    if (call_sym(h1, "mg_lane_x_open") != 0) return 5;
    if (call_sym(h2, "dy_core_open") != 0) return 6;
    if (call_sym(h2, "dy_lane_y_open") != 0) return 7;

    /* Keep dy_* entry points off the macro handle. */
    if (dlsym(h1, "dy_core_open") != NULL) {
        fprintf(stderr, "epsilon: macro leaks dy_core_open\n");
        return 8;
    }

    dlclose(h2);
    dlclose(h1);
    puts("epsilon:ok");
    return 0;
}
