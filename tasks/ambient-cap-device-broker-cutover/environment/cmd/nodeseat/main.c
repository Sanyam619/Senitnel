#include "../../seat/seat_slot_b.h"
#include <stdio.h>
#include <string.h>

int main(int argc, char **argv) {
    const char *src = NULL;
    const char *dst = NULL;
    const char *list = NULL;
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--src") == 0 && i + 1 < argc) src = argv[++i];
        else if (strcmp(argv[i], "--dst") == 0 && i + 1 < argc) dst = argv[++i];
        else if (strcmp(argv[i], "--names") == 0 && i + 1 < argc) list = argv[++i];
    }
    if (seat_slot_b(src, dst, list) != 0) {
        fprintf(stderr, "seat failed\n");
        return 1;
    }
    return 0;
}
