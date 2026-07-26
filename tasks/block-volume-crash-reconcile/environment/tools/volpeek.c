#include "kvfs_api.h"
#include "kvfs_layout.h"

#include <stdio.h>
#include <stdlib.h>

static void print_path(const char *name, uint32_t size, void *ctx) {
    (void)size;
    FILE *out = (FILE *)ctx;
    fprintf(out, "%s\n", name);
}

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: volpeek <image>\n");
        return 2;
    }
    kvfs_volume *vol = op_open_vol(argv[1]);
    if (!vol) { perror("open"); return 1; }
    uint32_t chosen = 0;
    if (resolve_c_pick_header(vol, &chosen)) {
        fprintf(stderr, "header pick failed\n");
        op_close_vol(vol);
        return 1;
    }
    uint64_t sealed = 0;
    step_a_scan_redo(vol, &sealed);
    printf("chosen_superblock=%u sealed_tx=%llu\n", chosen, (unsigned long long)sealed);
    r2_walk_inodes(vol, print_path, stdout);
    op_close_vol(vol);
    return 0;
}
