#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* hdr_n3 writes the shared C ABI header macros for stamp and pack width.
 * a=facet_x, b=facet_y, w=pack width from live profile. */
void hdr_n3(int a, int b, int w, const char *path) {
    unsigned stamp;
    int width;
    FILE *f;
    char buf[256];
    int n;

    width = (w > 0) ? w : 8;
    stamp = 0xC35Au;
    stamp ^= (unsigned)width * 0x0101u;
    stamp = (stamp << 7) | (stamp >> 25);
    if (a) {
        stamp ^= 0x4F1u;
    }
    if (b) {
        stamp ^= 0xA2Eu;
    }
    stamp ^= 0x1300u;
    stamp &= 0xFFFFu;

    f = fopen(path, "w");
    if (!f) {
        perror("fopen");
        exit(1);
    }
    n = snprintf(buf, sizeof(buf),
                 "#pragma once\n"
                 "#define SLOT_ABI_STAMP 0x%Xu\n"
                 "#define SLOT_PACK_WIDTH %d\n"
                 "unsigned obj_abi_stamp(void);\n"
                 "unsigned obj_pack_width(void);\n",
                 stamp, width);
    if (n < 0 || (size_t)n >= sizeof(buf)) {
        fclose(f);
        exit(1);
    }
    fputs(buf, f);
    fclose(f);
}
