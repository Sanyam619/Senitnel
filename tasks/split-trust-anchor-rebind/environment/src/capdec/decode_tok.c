#include "capdec.h"
#include <stdio.h>
#include <string.h>

static int tok_listed(const char *path, const char *tok) {
    FILE *fp = fopen(path, "r");
    if (!fp) {
        return 0;
    }
    char line[MAX_LINE];
    while (fgets(line, sizeof(line), fp)) {
        char *nl = strchr(line, '\n');
        if (nl) {
            *nl = '\0';
        }
        if (strcmp(line, tok) == 0) {
            fclose(fp);
            return 1;
        }
    }
    fclose(fp);
    return 0;
}

int load_rev_flags(const char *tok, int *in_current, int *in_cached) {
    if (!tok || !in_current || !in_cached) {
        return -1;
    }
    *in_current = tok_listed("/app/data/revocations/current.rl", tok);
    *in_cached = tok_listed("/app/data/revocations/cached.rl", tok);
    return 0;
}
