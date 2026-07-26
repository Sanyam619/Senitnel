#include "vault.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int read_u32_field(const char *path, const char *key, uint32_t *out) {
    FILE *fp = fopen(path, "r");
    if (!fp) {
        return -1;
    }
    char line[MAX_LINE];
    size_t klen = strlen(key);
    while (fgets(line, sizeof(line), fp)) {
        if (strncmp(line, key, klen) == 0 && line[klen] == '=') {
            *out = (uint32_t)strtoul(line + klen + 1, NULL, 10);
            fclose(fp);
            return 0;
        }
    }
    fclose(fp);
    return -1;
}

int load_store_meta(uint32_t *live_gen, uint32_t *restore_gen) {
    if (read_u32_field("/app/data/trust/live.bundle", "gen", live_gen) != 0) {
        return -1;
    }
    if (read_u32_field("/app/data/restore/trust.bundle", "gen", restore_gen) != 0) {
        return -1;
    }
    return 0;
}
