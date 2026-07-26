#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "frame.h"
#include "fold_q.h"
#include "skim_frame.h"
#include "wire.h"

static char *slurp(const char *path)
{
    FILE *fp = fopen(path, "rb");
    if (fp == NULL) {
        return NULL;
    }
    char *buf = (char *)malloc(WIRE_MAX + 1);
    if (buf == NULL) {
        fclose(fp);
        return NULL;
    }
    size_t n = fread(buf, 1, WIRE_MAX, fp);
    buf[n] = '\0';
    fclose(fp);
    return buf;
}

/* Return a heap copy of the value for `key=` on its own line, or NULL. */
static char *field(const char *buf, const char *key)
{
    size_t klen = strlen(key);
    const char *cur = buf;
    while (cur != NULL && *cur != '\0') {
        const char *nl = strchr(cur, '\n');
        size_t linelen = (nl != NULL) ? (size_t)(nl - cur) : strlen(cur);
        if (linelen > klen && strncmp(cur, key, klen) == 0 && cur[klen] == '=') {
            const char *val = cur + klen + 1;
            size_t vlen = linelen - klen - 1;
            char *out = (char *)malloc(vlen + 1);
            if (out == NULL) {
                return NULL;
            }
            memcpy(out, val, vlen);
            out[vlen] = '\0';
            return out;
        }
        cur = (nl != NULL) ? nl + 1 : NULL;
    }
    return NULL;
}

int main(int argc, char **argv)
{
    if (argc < 3) {
        fprintf(stderr, "usage: framectl <tip|skim> <record> [anchor]\n");
        return 2;
    }

    const char *mode = argv[1];
    const char *path = argv[2];
    char *buf = slurp(path);
    if (buf == NULL) {
        fprintf(stderr, "framectl: cannot read %s\n", path);
        return 2;
    }

    char *leaf = field(buf, WIRE_KEY_LEAF);
    char *parent = field(buf, WIRE_KEY_PARENT);
    char *sig = field(buf, WIRE_KEY_SIG);
    char *gens = field(buf, WIRE_KEY_GEN);
    long gen = (gens != NULL) ? atol(gens) : 0L;

    int rc = 0;
    if (strcmp(mode, "skim") == 0) {
        int ok = skim_frame(leaf, sig);
        printf(ok ? "OK\n" : "NOTOK\n");
    } else {
        const char *anchor = (argc >= 4) ? argv[3] : "";
        struct row_q a;
        a.leaf = leaf;
        a.parent = parent;
        a.anchor = anchor;
        a.sig = sig;
        a.gen = gen;

        struct slot_q b;
        memset(&b, 0, sizeof(b));
        fold_q(&a, &b);

        printf("{\"leaf\":\"%s\",\"parent\":\"%s\",\"gen\":%ld,"
               "\"sig_ok\":%s,\"tip_ok\":%s}\n",
               (leaf != NULL) ? leaf : "",
               (parent != NULL) ? parent : "",
               gen,
               b.sig_ok ? "true" : "false",
               b.tip_ok ? "true" : "false");
    }

    free(leaf);
    free(parent);
    free(sig);
    free(gens);
    free(buf);
    return rc;
}
