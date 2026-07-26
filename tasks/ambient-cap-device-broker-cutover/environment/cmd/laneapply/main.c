#include "../../lane/apply_lane_a.h"
#include "../../lane/legacy_lane.h"
#include <stdio.h>
#include <string.h>

int main(int argc, char **argv) {
    const char *mode = "lane";
    const char *root = NULL;
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--legacy") == 0) mode = "legacy";
        else if (strcmp(argv[i], "--root") == 0 && i + 1 < argc) root = argv[++i];
    }
    if (strcmp(mode, "legacy") == 0) {
        if (legacy_lane(root) != 0) {
            fprintf(stderr, "legacy failed\n");
            return 1;
        }
        return 0;
    }
    if (apply_lane_a(root, "") != 0) {
        fprintf(stderr, "lane failed\n");
        return 1;
    }
    return 0;
}
