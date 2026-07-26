#include "../../include/lab.h"
#include "../../lib/state_io.h"
#include <stdio.h>
#include <string.h>
#include <unistd.h>

int main(int argc, char **argv) {
    const char *names = NULL;
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--names") == 0 && i + 1 < argc) names = argv[++i];
    }
    if (!names) {
        fprintf(stderr, "usage: unseat --names <csv>\n");
        return 1;
    }

    char buf[512];
    snprintf(buf, sizeof(buf), "%s", names);
    char *save = NULL;
    for (char *tok = strtok_r(buf, ",", &save); tok; tok = strtok_r(NULL, ",", &save)) {
        char bt[512], ht[512], bm[512], hm[512];
        snprintf(bt, sizeof(bt), "%s/%s", BROKER_TREE, tok);
        snprintf(ht, sizeof(ht), "%s/%s", HOST_TREE, tok);
        snprintf(bm, sizeof(bm), "%s/%s", BROKER_MARKS, tok);
        snprintf(hm, sizeof(hm), "%s/%s", HOST_MARKS, tok);

        if (!file_exists(bt) && !file_exists(bm)) {
            fprintf(stderr, "unseat: %s not in broker\n", tok);
            return 1;
        }
        if (file_exists(ht)) {
            fprintf(stderr, "unseat: %s already has host tree entry\n", tok);
            return 1;
        }

        ensure_dir(HOST_TREE);
        ensure_dir(HOST_MARKS);
        char body[256];
        snprintf(body, sizeof(body), "watch:%s", tok);
        if (write_text(ht, body) != 0) return -1;
        if (write_text(hm, "inode") != 0) return -1;
        if (file_exists(bt)) unlink(bt);
        if (file_exists(bm)) unlink(bm);
    }
    printf("unseated: %s\n", names);
    return 0;
}
