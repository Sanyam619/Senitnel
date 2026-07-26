#include <string.h>

#include "sieve_b.h"

int sieve_b(int a, const char *b, const char *c)
{
    if (a == 0) {
        return 0;
    }
    if (b == NULL || b[0] == '\0') {
        return 0;
    }
    if (strcmp(b, "open") == 0) {
        return 1;
    }
    if (strcmp(b, "exec") == 0) {
        if (c != NULL && strcmp(c, "hold") == 0) {
            return 0;
        }
        if (c != NULL && strcmp(c, "pass") == 0) {
            return 1;
        }
        return 0;
    }
    return 0;
}
