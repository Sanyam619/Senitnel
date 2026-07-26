#include "pinset.h"
#include <stdio.h>
#include <string.h>

int probe_hot(const char *claim, char *out, size_t n) {
    if (!claim || !out || n == 0) {
        return -1;
    }
    snprintf(out, n, "hot:%s", claim);
    return 0;
}
