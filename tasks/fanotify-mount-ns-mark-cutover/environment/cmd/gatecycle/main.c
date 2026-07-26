#include "../../gate/cycle_gate_b.h"
#include "../../gate/probe_gate.h"
#include <stdio.h>
#include <string.h>

int main(int argc, char **argv) {
    const char *mode = "cycle";
    const char *a = NULL;
    const char *b = NULL;
    const char *c = NULL;
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--probe") == 0) mode = "probe";
        else if (strcmp(argv[i], "--src") == 0 && i + 1 < argc) a = argv[++i];
        else if (strcmp(argv[i], "--dst") == 0 && i + 1 < argc) b = argv[++i];
        else if (strcmp(argv[i], "--names") == 0 && i + 1 < argc) c = argv[++i];
    }
    if (strcmp(mode, "probe") == 0) {
        return probe_gate(a) == 0 ? 0 : 1;
    }
    if (cycle_gate_b(a, b, c) != 0) {
        fprintf(stderr, "cycle failed\n");
        return 1;
    }
    return 0;
}
