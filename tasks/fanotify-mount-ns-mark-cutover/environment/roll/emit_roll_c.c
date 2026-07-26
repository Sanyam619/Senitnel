#include "emit_roll_c.h"
#include "../include/lab.h"
#include "../lib/state_io.h"
#include <stdio.h>
#include <string.h>

static int fold_one(const char *path) {
    char buf[8192];
    if (read_text(path, buf, sizeof(buf)) != 0) return -1;
    if (strstr(buf, "PrivateMounts=yes") == NULL) return 0;
    char result[8192];
    const char *p = buf;
    size_t o = 0;
    while (*p && o + 1 < sizeof(result)) {
        if (strncmp(p, "PrivateMounts=yes", 17) == 0) {
            const char *rep = "PrivateMounts=no";
            size_t n = strlen(rep);
            memcpy(result + o, rep, n);
            o += n;
            p += 17;
            continue;
        }
        result[o++] = *p++;
    }
    result[o] = 0;
    return write_text(path, result);
}

int emit_roll_c(const char *action, const char *out_path) {
    if (!action) return -1;

    if (strcmp(action, "fold") == 0) {
        return fold_one(UNIT_LIVE);
    }

    if (strcmp(action, "emit") == 0) {
        const char *dest = (out_path && out_path[0]) ? out_path : OUT_DEFAULT;
        char race[64];
        if (read_text(RACE_FLAG, race, sizeof(race)) != 0)
            snprintf(race, sizeof(race), "dirty");
        int stable = (strcmp(race, "clean") == 0);

        char ok_buf[32];
        if (read_text(INHERIT_OK, ok_buf, sizeof(ok_buf)) != 0)
            snprintf(ok_buf, sizeof(ok_buf), "0");
        int inherit_ok = (strcmp(ok_buf, "1") == 0);

        char table[4096];
        table[0] = 0;
        read_text(INHERIT_TABLE, table, sizeof(table));

        char body[8192];
        size_t o = 0;
        o += (size_t)snprintf(body + o, sizeof(body) - o,
            "{\n  \"version\": 1,\n  \"watches\": [\n");

        for (int i = 0; i < NUM_PATHS; i++) {
            const char *name = ALL_PATHS[i];
            char bm[512], hm[512], bt[512], ht[512];
            snprintf(bm, sizeof(bm), "%s/%s", BROKER_MARKS, name);
            snprintf(hm, sizeof(hm), "%s/%s", HOST_MARKS, name);
            snprintf(bt, sizeof(bt), "%s/%s", BROKER_TREE, name);
            snprintf(ht, sizeof(ht), "%s/%s", HOST_TREE, name);

            const char *ns = "unknown";
            char kind[64];
            kind[0] = 0;

            if (file_exists(bt) && file_exists(bm)) {
                ns = "broker";
                read_text(bm, kind, sizeof(kind));
            } else if (file_exists(ht) && file_exists(hm)) {
                ns = "host";
                read_text(hm, kind, sizeof(kind));
            } else if (file_exists(bm)) {
                ns = "broker";
                read_text(bm, kind, sizeof(kind));
            } else if (file_exists(hm)) {
                ns = "host";
                read_text(hm, kind, sizeof(kind));
            }

            char token[128];
            snprintf(token, sizeof(token), "%s:remount-ok", name);
            int path_inherited = inherit_ok && (strstr(table, token) != NULL);

            char jp[512];
            snprintf(jp, sizeof(jp), "%s/%s", HOST_JITTER, name);
            int path_stable = stable && !file_exists(jp);

            if (i > 0)
                o += (size_t)snprintf(body + o, sizeof(body) - o, ",\n");
            o += (size_t)snprintf(body + o, sizeof(body) - o,
                "    {\"path\": \"%s\", \"mark_ns\": \"%s\", \"mark_kind\": \"%s\", "
                "\"inherited_ok\": %s, \"race_stable\": %s}",
                name, ns, kind,
                path_inherited ? "true" : "false",
                path_stable ? "true" : "false");
        }

        o += (size_t)snprintf(body + o, sizeof(body) - o, "\n  ]\n}\n");
        ensure_dir("/output");
        return write_text(dest, body);
    }

    return -1;
}
