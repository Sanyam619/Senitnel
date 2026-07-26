#include "path_util.h"
#include <stdio.h>

int join3(char *out, int n, const char *a, const char *b, const char *c) {
    if (!out || n <= 0 || !a || !b || !c) return -1;
    int k = snprintf(out, (size_t)n, "%s/%s/%s", a, b, c);
    if (k < 0 || k >= n) return -1;
    return 0;
}
