#include "probe_gate.h"
#include "../include/lab.h"
#include "../lib/state_io.h"
#include <stdio.h>

int probe_gate(const char *a) {
    (void)a;
    char buf[4096];
    if (read_text(INHERIT_TABLE, buf, sizeof(buf)) != 0) {
        printf("(empty)\n");
        return 0;
    }
    if (buf[0] == 0) {
        printf("(empty)\n");
    } else {
        printf("%s\n", buf);
    }
    return 0;
}
