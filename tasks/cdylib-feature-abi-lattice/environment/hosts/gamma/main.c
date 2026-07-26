#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>

typedef int (*nx_fn)(void);

int main(int argc, char **argv) {
    const char *path = argc > 1 ? argv[1] : "libnuclide.so";
    void *h = dlopen(path, RTLD_NOW | RTLD_LOCAL);
    if (!h) {
        fprintf(stderr, "gamma: dlopen failed: %s\n", dlerror());
        return 2;
    }
    nx_fn open_fn = (nx_fn)dlsym(h, "nx_trunk_open");
    if (!open_fn) {
        fprintf(stderr, "gamma: missing nx_trunk_open: %s\n", dlerror());
        return 3;
    }
    if (open_fn() < 0) {
        fprintf(stderr, "gamma: nx_trunk_open failed\n");
        return 4;
    }
    dlclose(h);
    puts("gamma:ok");
    return 0;
}
