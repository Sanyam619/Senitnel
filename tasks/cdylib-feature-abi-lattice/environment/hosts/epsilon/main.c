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
    int rc = fn();
    if (rc < 0) {
        fprintf(stderr, "epsilon: %s returned %d\n", name, rc);
        return 1;
    }
    return 0;
}

int main(int argc, char **argv) {
    const char *nuclide_path = argc > 1 ? argv[1] : "libnuclide.so";
    const char *cascade_path = argc > 2 ? argv[2] : "libcascade.so";

    void *h1 = dlopen(nuclide_path, RTLD_NOW | RTLD_LOCAL);
    if (!h1) {
        fprintf(stderr, "epsilon: nuclide dlopen failed: %s\n", dlerror());
        return 2;
    }

    void *h2 = dlopen(cascade_path, RTLD_NOW | RTLD_LOCAL);
    if (!h2) {
        fprintf(stderr, "epsilon: cascade dlopen failed: %s\n", dlerror());
        dlclose(h1);
        return 3;
    }

    /* nuclide symbols */
    if (call_sym(h1, "nx_trunk_open") != 0) {
        return 4;
    }
    if (call_sym(h1, "nx_facet_a_open") != 0) {
        return 5;
    }

    /* cascade symbols */
    if (call_sym(h2, "cx_trunk_open") != 0) {
        return 6;
    }
    if (call_sym(h2, "cx_facet_c_open") != 0) {
        return 7;
    }

    /* cascade must not re-export nuclide's nx_facet_a_open */
    if (dlsym(h2, "nx_facet_a_open") != NULL) {
        fprintf(stderr, "epsilon: cascade leaks nx_facet_a_open\n");
        return 8;
    }

    dlclose(h2);
    dlclose(h1);
    puts("epsilon:ok");
    return 0;
}
