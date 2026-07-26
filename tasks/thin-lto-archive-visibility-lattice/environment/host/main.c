#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>

#include "slot_vis.h"
#include "obj_api.h"

typedef unsigned (*u_fn)(void);

int main(int argc, char **argv) {
    const char *lib = argc > 1 ? argv[1] : "libr7.so";
    void *h = dlopen(lib, RTLD_NOW);
    u_fn rdig;
    u_fn repoch;
    unsigned rd, re, cd, ce, cm;

    if (!h) {
        fprintf(stderr, "dlopen: %s\n", dlerror());
        return 1;
    }
    rdig = (u_fn)dlsym(h, "nx_vis_digest");
    repoch = (u_fn)dlsym(h, "nx_bitcode_epoch");
    if (!rdig || !repoch) {
        fprintf(stderr, "dlsym missing\n");
        return 1;
    }
    rd = rdig();
    re = repoch();
    cd = obj_vis_digest();
    ce = obj_bitcode_epoch();
    cm = obj_archive_members();

    printf("{\"rust\":{\"vis_digest\":%u,\"bitcode_epoch\":%u},"
           "\"c\":{\"vis_digest\":%u,\"bitcode_epoch\":%u,\"archive_members\":%u},"
           "\"header\":{\"vis_digest\":%u,\"bitcode_epoch\":%d}}\n",
           rd, re, cd, ce, cm,
           (unsigned)SLOT_VIS_DIGEST, SLOT_BITCODE_EPOCH);
    dlclose(h);
    return 0;
}
