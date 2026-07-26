#include <dlfcn.h>
#include <stdio.h>

typedef int (*fn_i)(void);

int load_slot(const char *path, int *abi_out, int *frame_out) {
    void *h = dlopen(path, RTLD_NOW);
    if (!h) {
        fprintf(stderr, "dlopen: %s\n", dlerror());
        return 10;
    }
    fn_i open_fn = (fn_i)dlsym(h, "slot_open");
    fn_i abi_fn = (fn_i)dlsym(h, "slot_abi_version");
    fn_i frame_fn = (fn_i)dlsym(h, "slot_frame_size");
    fn_i close_fn = (fn_i)dlsym(h, "slot_close");
    if (!open_fn || !abi_fn || !frame_fn || !close_fn) {
        dlclose(h);
        return 11;
    }
    if (open_fn() < 0) {
        dlclose(h);
        return 12;
    }
    *abi_out = abi_fn();
    *frame_out = frame_fn();
    close_fn();
    dlclose(h);
    return 0;
}
