#include <stddef.h>

#include "skim_sieve.h"

int skim_sieve(int a, const char *b, const char *c)
{
    (void)a;
    (void)c;
    if (b != NULL && b[0] != '\0') {
        return 1;
    }
    return 0;
}
