#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>

typedef int (*nx_fn)(void);

static int call_sym(void *h, const char *name) {
    nx_fn fn = (nx_fn)dlsym(h, name);
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
    const char *path = argc > 1 ? argv[1] : "libnuclide.so";
    void *h = dlopen(path, RTLD_NOW | RTLD_LOCAL);
    if (!h) {
        fprintf(stderr, "alpha: dlopen failed: %s\n", dlerror());
        return 2;
    }
    if (call_sym(h, "nx_trunk_open") != 0) {
        return 3;
    }
    if (call_sym(h, "nx_facet_a_open") != 0) {
        return 4;
    }
    /* Primary lane requires the v2 ABI tag export. */
    if (call_sym(h, "nx_abi_tag_v2") != 0) {
        return 5;
    }
    if (dlsym(h, "nx_abi_tag_v1") != NULL) {
        fprintf(stderr, "alpha: unexpected legacy nx_abi_tag_v1 present\n");
        return 6;
    }
    dlclose(h);
    puts("alpha:ok");
    return 0;
}
