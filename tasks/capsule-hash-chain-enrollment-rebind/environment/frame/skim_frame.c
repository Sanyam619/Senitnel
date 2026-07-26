#include <stddef.h>

#include "skim_frame.h"

/*
 * Leaf-surface skim: folds the leaf token into a 64-bit rolling hash and
 * confirms a marker byte is present. This is the shallow view surfcheck
 * uses; it does not inspect any continuity beyond the leaf itself.
 */
int skim_frame(const char *leaf, const char *sig)
{
    if (leaf == NULL || leaf[0] == '\0') {
        return 0;
    }

    unsigned long h = 1469598103934665603UL;
    for (const char *p = leaf; *p != '\0'; ++p) {
        h ^= (unsigned char)*p;
        h *= 1099511628211UL;
    }

    int sig_present = (sig != NULL && sig[0] != '\0');
    return sig_present && (h != 0UL);
}
