#include "cycle_gate_b.h"
#include "../include/lab.h"
#include "../lib/state_io.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int cmp_str(const void *a, const void *b) {
    return strcmp(*(const char *const *)a, *(const char *const *)b);
}

int cycle_gate_b(const char *a, const char *b, const char *names_csv) {
    (void)a;
    (void)b;
    if (!names_csv || !names_csv[0]) return -1;

    char mnt[64];
    if (read_text(MNT_ID, mnt, sizeof(mnt)) != 0) return -1;
    if (strcmp(mnt, "broker") != 0) {
        fprintf(stderr, "gatecycle: identity not broker\n");
        return -1;
    }

    char unit[4096];
    if (read_text(UNIT_LIVE, unit, sizeof(unit)) != 0) return -1;
    if (strstr(unit, "PrivateMounts=yes") != NULL) {
        fprintf(stderr, "gatecycle: PrivateMounts still yes\n");
        return -1;
    }

    char *names[32];
    int nnames = 0;
    char buf[512];
    snprintf(buf, sizeof(buf), "%s", names_csv);
    char *save = NULL;
    for (char *tok = strtok_r(buf, ",", &save); tok && nnames < 32; tok = strtok_r(NULL, ",", &save)) {
        names[nnames++] = tok;
    }
    qsort(names, (size_t)nnames, sizeof(char *), cmp_str);

    ensure_dir("/data/lab/inherit");
    char table[2048];
    size_t o = 0;
    table[0] = 0;

    for (int i = 0; i < nnames; i++) {
        char *tok = names[i];
        char bm[512], kind[64];
        snprintf(bm, sizeof(bm), "%s/%s", BROKER_MARKS, tok);
        if (!file_exists(bm)) {
            fprintf(stderr, "gatecycle: %s has no broker mark\n", tok);
            return -1;
        }
        if (read_text(bm, kind, sizeof(kind)) != 0) return -1;
        if (strcmp(kind, "filesystem") != 0) {
            fprintf(stderr, "gatecycle: %s mark is %s, need filesystem\n", tok, kind);
            return -1;
        }
        char ht[512];
        snprintf(ht, sizeof(ht), "%s/%s", HOST_TREE, tok);
        if (file_exists(ht)) {
            fprintf(stderr, "gatecycle: %s still has host tree entry\n", tok);
            return -1;
        }
        int n = snprintf(table + o, sizeof(table) - o, "%s%s:remount-ok",
                         o ? "\n" : "", tok);
        if (n < 0 || (size_t)n >= sizeof(table) - o) return -1;
        o += (size_t)n;
    }

    if (write_text(INHERIT_TABLE, table) != 0) return -1;
    if (write_text(INHERIT_OK, "1") != 0) return -1;
    return 0;
}
