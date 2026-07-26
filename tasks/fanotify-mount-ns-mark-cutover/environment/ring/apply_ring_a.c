#include "apply_ring_a.h"
#include "../include/lab.h"
#include "../lib/state_io.h"
#include <stdio.h>
#include <string.h>
#include <unistd.h>

int apply_ring_a(const char *names_csv, const char *kind) {
    if (!names_csv || !names_csv[0]) return -1;
    (void)kind;

    char buf[512];
    snprintf(buf, sizeof(buf), "%s", names_csv);
    char *save = NULL;
    for (char *tok = strtok_r(buf, ",", &save); tok; tok = strtok_r(NULL, ",", &save)) {
        char bt[512], ht[512], bm[512], hm[512];
        snprintf(bt, sizeof(bt), "%s/%s", BROKER_TREE, tok);
        snprintf(ht, sizeof(ht), "%s/%s", HOST_TREE, tok);
        snprintf(bm, sizeof(bm), "%s/%s", BROKER_MARKS, tok);
        snprintf(hm, sizeof(hm), "%s/%s", HOST_MARKS, tok);

        if (file_exists(bt)) {
            fprintf(stderr, "seat: %s already in broker tree\n", tok);
            return -1;
        }
        if (!file_exists(ht)) {
            fprintf(stderr, "seat: %s not in host tree\n", tok);
            return -1;
        }

        char body[256];
        read_text(ht, body, sizeof(body));

        char mk[64];
        snprintf(mk, sizeof(mk), "inode");
        if (file_exists(hm)) read_text(hm, mk, sizeof(mk));

        ensure_dir(BROKER_TREE);
        ensure_dir(BROKER_MARKS);
        if (write_text(bt, body) != 0) return -1;
        if (write_text(bm, mk) != 0) return -1;
        unlink(ht);
        if (file_exists(hm)) unlink(hm);
    }

    ensure_dir("/data/lab/identity");
    write_text(MNT_ID, "broker");
    return 0;
}
