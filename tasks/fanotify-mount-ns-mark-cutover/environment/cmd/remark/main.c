#include "../../include/lab.h"
#include "../../lib/state_io.h"
#include <stdio.h>
#include <string.h>

int main(int argc, char **argv) {
    const char *path_name = NULL;
    const char *kind = NULL;
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--path") == 0 && i + 1 < argc) path_name = argv[++i];
        else if (strcmp(argv[i], "--kind") == 0 && i + 1 < argc) kind = argv[++i];
    }
    if (!path_name || !kind) {
        fprintf(stderr, "usage: remark --path <name> --kind <filesystem|inode>\n");
        return 1;
    }

    char bm[512], hm[512];
    snprintf(bm, sizeof(bm), "%s/%s", BROKER_MARKS, path_name);
    snprintf(hm, sizeof(hm), "%s/%s", HOST_MARKS, path_name);

    if (file_exists(bm)) {
        if (write_text(bm, kind) != 0) return 1;
        printf("remarked %s in broker: %s\n", path_name, kind);
        return 0;
    }
    if (file_exists(hm)) {
        if (write_text(hm, kind) != 0) return 1;
        printf("remarked %s in host: %s\n", path_name, kind);
        return 0;
    }
    fprintf(stderr, "remark: %s has no mark in any namespace\n", path_name);
    return 1;
}
