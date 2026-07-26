#include "../../roll/emit_rollup_c.h"
#include <stdio.h>
#include <string.h>

int main(int argc, char **argv) {
    const char *mode = NULL;
    const char *out = NULL;
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--fold") == 0) mode = "fold";
        else if (strcmp(argv[i], "--emit") == 0) mode = "emit";
        else if (strcmp(argv[i], "--out") == 0 && i + 1 < argc) out = argv[++i];
    }
    if (!mode) {
        fprintf(stderr, "usage: ledgerout --fold | --emit [--out path]\n");
        return 2;
    }
    if (emit_rollup_c(mode, out) != 0) {
        fprintf(stderr, "rollup failed\n");
        return 1;
    }
    return 0;
}
