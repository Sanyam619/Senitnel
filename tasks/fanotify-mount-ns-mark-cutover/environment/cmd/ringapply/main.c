#include "../../ring/apply_ring_a.h"
#include "../../ring/legacy_ring.h"
#include <stdio.h>
#include <string.h>

int main(int argc, char **argv) {
    const char *mode = "ring";
    const char *names = NULL;
    const char *kind = "filesystem";
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--legacy") == 0) mode = "legacy";
        else if (strcmp(argv[i], "--names") == 0 && i + 1 < argc) names = argv[++i];
        else if (strcmp(argv[i], "--kind") == 0 && i + 1 < argc) kind = argv[++i];
    }
    if (strcmp(mode, "legacy") == 0) {
        if (legacy_ring(NULL) != 0) {
            fprintf(stderr, "legacy failed\n");
            return 1;
        }
        return 0;
    }
    if (!names) {
        fprintf(stderr, "usage: ringapply --names <csv> [--kind filesystem|inode]\n");
        return 1;
    }
    if (apply_ring_a(names, kind) != 0) {
        fprintf(stderr, "ring failed\n");
        return 1;
    }
    printf("seated: %s (kind=%s)\n", names, kind);
    return 0;
}
