#include "capdec.h"
#include <stdio.h>

int cache_view(const char *tok, char *out, size_t n) {
    if (!tok || !out || n == 0) {
        return -1;
    }
    snprintf(out, n, "view:%s", tok);
    return 0;
}
