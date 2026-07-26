#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>

#include "slot_abi.h"
#include "obj_api.h"

typedef unsigned (*u_fn)(void);

int main(int argc, char **argv) {
    const char *lib = argc > 1 ? argv[1] : "libr8.so";
    void *h = dlopen(lib, RTLD_NOW);
    u_fn rstamp;
    u_fn rpack;
    unsigned rs, rp, cs, cp;

    if (!h) {
        fprintf(stderr, "dlopen: %s\n", dlerror());
        return 1;
    }
    rstamp = (u_fn)dlsym(h, "nx_abi_stamp");
    rpack = (u_fn)dlsym(h, "nx_pack_width");
    if (!rstamp || !rpack) {
        fprintf(stderr, "dlsym missing\n");
        return 1;
    }
    rs = rstamp();
    rp = rpack();
    cs = obj_abi_stamp();
    cp = obj_pack_width();

    printf("{\"rust\":{\"abi_stamp\":%u,\"pack_width\":%u},"
           "\"c\":{\"abi_stamp\":%u,\"pack_width\":%u},"
           "\"header\":{\"abi_stamp\":%u,\"pack_width\":%d}}\n",
           rs, rp, cs, cp, (unsigned)SLOT_ABI_STAMP, SLOT_PACK_WIDTH);
    dlclose(h);
    return 0;
}
