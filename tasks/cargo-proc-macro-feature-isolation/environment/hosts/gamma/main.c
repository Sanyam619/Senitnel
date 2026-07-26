#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>

typedef int (*sym_fn)(void);

int main(int argc, char **argv) {
    const char *path = argc > 1 ? argv[1] : "libflux_cdylib.so";
    void *h = dlopen(path, RTLD_NOW | RTLD_LOCAL);
    if (!h) {
        fprintf(stderr, "gamma: dlopen failed: %s\n", dlerror());
        return 2;
    }
    sym_fn core = (sym_fn)dlsym(h, "dy_core_open");
    if (!core) {
        fprintf(stderr, "gamma: missing dy_core_open\n");
        return 3;
    }
    if (core() < 0) return 4;
    dlclose(h);
    puts("gamma:ok");
    return 0;
}
