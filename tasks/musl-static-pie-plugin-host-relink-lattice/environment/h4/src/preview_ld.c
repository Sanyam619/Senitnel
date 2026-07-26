/* Pretty-prints historical LD fragments for ops docs; not invoked by release host builds. */
#include <stdio.h>

void preview_ld_fragment(const char *a) {
    printf("legacy-ld:%s\n", a ? a : "");
}
