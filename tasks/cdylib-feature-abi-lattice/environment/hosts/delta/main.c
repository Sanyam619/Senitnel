#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>

typedef int (*cx_fn)(void);

static int call_sym(void *h, const char *name) {
    cx_fn fn = (cx_fn)dlsym(h, name);
    if (!fn) {
        fprintf(stderr, "delta: missing %s: %s\n", name, dlerror());
        return 1;
    }
    int rc = fn();
    if (rc < 0) {
        fprintf(stderr, "delta: %s returned %d\n", name, rc);
        return 1;
    }
    return 0;
}

int main(int argc, char **argv) {
    const char *path = argc > 1 ? argv[1] : "libcascade.so";
    void *h = dlopen(path, RTLD_NOW | RTLD_LOCAL);
    if (!h) {
        fprintf(stderr, "delta: dlopen failed: %s\n", dlerror());
        return 2;
    }
    if (call_sym(h, "cx_trunk_open") != 0) {
        return 3;
    }
    if (call_sym(h, "cx_facet_c_open") != 0) {
        return 4;
    }
    if (call_sym(h, "cx_abi_tag_c1") != 0) {
        return 5;
    }
    /* cascade must not re-export nuclide symbols */
    if (dlsym(h, "nx_trunk_open") != NULL) {
        fprintf(stderr, "delta: unexpected nx_trunk_open in cascade\n");
        return 6;
    }
    if (dlsym(h, "nx_facet_a_open") != NULL) {
        fprintf(stderr, "delta: unexpected nx_facet_a_open in cascade\n");
        return 7;
    }
    dlclose(h);
    puts("delta:ok");
    return 0;
}
