#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* emit_q3 writes visibility map macros for digest and bitcode epoch.
 * a=strand_a, b=strand_b, e=epoch from live profile, m=archive members. */
void emit_q3(int a, int b, int e, int m, const char *path) {
    unsigned dig;
    unsigned epoch;
    unsigned members;
    unsigned s;
    FILE *f;
    char buf[320];
    char tmp[384];
    int n;

    epoch = (e > 0) ? (unsigned)e : 3u;
    members = (m > 0) ? (unsigned)m : 4u;
    s = 0xA7E3u;
    s ^= epoch * 0x1051u;
    s = (s << 7) | (s >> 25);
    s ^= (members + 1u) * 0x21Bu;
    s = (s << 11) | (s >> 21);
    if (a) {
        s ^= 0x8C5u;
    }
    if (b) {
        s ^= 0xD2Fu;
    }
    s ^= 0x4400u;
    dig = s & 0xFFFFu;

    n = snprintf(tmp, sizeof(tmp), "%s.tmp", path);
    if (n < 0 || (size_t)n >= sizeof(tmp)) {
        exit(1);
    }
    f = fopen(tmp, "w");
    if (!f) {
        perror("fopen");
        exit(1);
    }
    n = snprintf(buf, sizeof(buf),
                 "#pragma once\n"
                 "#define SLOT_VIS_DIGEST 0x%Xu\n"
                 "#define SLOT_BITCODE_EPOCH %u\n"
                 "unsigned obj_vis_digest(void);\n"
                 "unsigned obj_bitcode_epoch(void);\n"
                 "unsigned obj_archive_members(void);\n",
                 dig, epoch);
    if (n < 0 || (size_t)n >= sizeof(buf)) {
        fclose(f);
        exit(1);
    }
    if (fputs(buf, f) < 0) {
        fclose(f);
        exit(1);
    }
    if (fclose(f) != 0) {
        exit(1);
    }
    if (rename(tmp, path) != 0) {
        perror("rename");
        exit(1);
    }
}
