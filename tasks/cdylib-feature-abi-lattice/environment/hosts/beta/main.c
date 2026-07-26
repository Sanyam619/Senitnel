#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>

typedef int (*nx_fn)(void);

static int call_sym(void *h, const char *name) {
    nx_fn fn = (nx_fn)dlsym(h, name);
    if (!fn) {
        fprintf(stderr, "beta: missing %s: %s\n", name, dlerror());
        return 1;
    }
    int rc = fn();
    if (rc < 0) {
        fprintf(stderr, "beta: %s returned %d\n", name, rc);
        return 1;
    }
    return 0;
}

int main(int argc, char **argv) {
    const char *path = argc > 1 ? argv[1] : "libnuclide.so";
    void *h = dlopen(path, RTLD_NOW | RTLD_LOCAL);
    if (!h) {
        fprintf(stderr, "beta: dlopen failed: %s\n", dlerror());
        return 2;
    }
    if (call_sym(h, "nx_trunk_open") != 0) {
        return 3;
    }
    if (call_sym(h, "nx_facet_b_open") != 0) {
        return 4;
    }
    if (dlsym(h, "nx_facet_a_open") != NULL) {
        fprintf(stderr, "beta: unexpected nx_facet_a_open present\n");
        return 5;
    }
    if (dlsym(h, "nx_abi_tag_v2") != NULL) {
        fprintf(stderr, "beta: unexpected nx_abi_tag_v2 present\n");
        return 6;
    }
    dlclose(h);
    puts("beta:ok");
    return 0;
}
