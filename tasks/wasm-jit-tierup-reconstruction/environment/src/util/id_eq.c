#include "common.h"
#include <string.h>

int util_id_eq(const char *a, const char *b) {
    if (!a || !b) return 0;
    return strcmp(a, b) == 0;
}
