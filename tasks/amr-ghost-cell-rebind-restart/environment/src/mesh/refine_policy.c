#include "mesh.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int parse_kv(const char *line, const char *key, char *out, size_t out_len) {
    size_t klen = strlen(key);
    if (strncmp(line, key, klen) != 0 || line[klen] != '=') {
        return 0;
    }
    const char *val = line + klen + 1;
    snprintf(out, out_len, "%s", val);
    return 1;
}

int mesh_load_policy(const char *path, const char *label, mesh_ctx_t *m);

int refine_policy_read(const char *path, const char *label, mesh_ctx_t *m) {
    FILE *fp = fopen(path, "r");
    if (!fp || !m) {
        return -1;
    }
    char line[256];
    char section[64] = "";
    char want[64];
    snprintf(want, sizeof(want), "[%s]", label);
    while (fgets(line, sizeof(line), fp)) {
        if (line[0] == '[') {
            snprintf(section, sizeof(section), "%.*s", (int)strcspn(line, "\n"), line);
            continue;
        }
        if (strcmp(section, want) != 0) {
            continue;
        }
        char buf[64];
        if (parse_kv(line, "blocks", buf, sizeof(buf))) {
            m->block_tally = atoi(buf);
        } else if (parse_kv(line, "depth", buf, sizeof(buf))) {
            m->tree_depth = atoi(buf);
        }
    }
    fclose(fp);
    return 0;
}

int mesh_load_policy(const char *path, const char *label, mesh_ctx_t *m) {
    if (!m) {
        return -1;
    }
    m->block_tally = 0;
    m->tree_depth = 0;
    m->link_gen = 0;
    m->links_ready = 0;
    m->layout_ready = 0;
    return refine_policy_read(path, label, m);
}
