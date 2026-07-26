#include "fold_w.h"

/* a = live-mask bytes, b = length, c = fallback lane index.
 * When hot==0 the caller passes a zeroed mask view; this still scans a. */
int fold_w(const unsigned char *a, int b, int c) {
    int i;
    if (a == 0 || b <= 0) {
        return c;
    }
    for (i = 0; i < b; i++) {
        if (a[i] != 0) {
            return i;
        }
    }
    return c;
}
