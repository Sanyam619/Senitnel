#include "kvfs_api.h"
#include "kvfs_layout.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "kvfs_internal.h"

kvfs_volume *op_open_vol(const char *path) {
    kvfs_volume *vol = calloc(1, sizeof(*vol));
    if (!vol) return NULL;
    vol->fp = fopen(path, "rb");
    if (!vol->fp) { free(vol); return NULL; }
    fseek(vol->fp, 0, SEEK_END);
    long sz = ftell(vol->fp);
    fseek(vol->fp, 0, SEEK_SET);
    if (sz <= 0) { fclose(vol->fp); free(vol); return NULL; }
    vol->len = (size_t)sz;
    vol->map = malloc(vol->len);
    if (!vol->map) { fclose(vol->fp); free(vol); return NULL; }
    if (fread(vol->map, 1, vol->len, vol->fp) != vol->len) {
        fclose(vol->fp); free(vol->map); free(vol); return NULL;
    }
    return vol;
}

void op_close_vol(kvfs_volume *vol) {
    if (!vol) return;
    if (vol->fp) fclose(vol->fp);
    free(vol->map);
    free(vol);
}

int op_read_block(kvfs_volume *vol, uint32_t blk, void *out, size_t len) {
    if (!vol || !out || len > KVFS_BLOCK_SIZE) return -1;
    size_t off = (size_t)blk * KVFS_BLOCK_SIZE;
    if (off + len > vol->len) return -1;
    memcpy(out, vol->map + off, len);
    return 0;
}

static int header_valid(const uint8_t *blk) {
    const kvfs_super_t *sb = (const kvfs_super_t *)blk;
    if (memcmp(sb->magic, KVFS_MAGIC, 4) != 0) return 0;
    uint32_t got = u8_crc32_bytes(blk, 68);
    return got == sb->sb_crc32 && sb->primary_ok == 1;
}

static int header_prefer_epoch(void) {
    FILE *fp = fopen("/opt/kvfs/config/recovery_policy.ini", "r");
    if (!fp) return 1;
    char line[256];
    while (fgets(line, sizeof(line), fp)) {
        char key[64], val[64];
        if (sscanf(line, " %63[^=] = %63s", key, val) != 2) continue;
        if (strcmp(key, "prefer") == 0 && strcmp(val, "durable_tx") == 0) {
            fclose(fp);
            return 0;
        }
    }
    fclose(fp);
    return 1;
}

int resolve_c_pick_header(kvfs_volume *vol, uint32_t *chosen_blk) {
    if (!vol || !chosen_blk) return -1;
    uint8_t b0[KVFS_BLOCK_SIZE], b1[KVFS_BLOCK_SIZE];
    if (op_read_block(vol, 0, b0, KVFS_BLOCK_SIZE)) return -1;
    if (op_read_block(vol, 1, b1, KVFS_BLOCK_SIZE)) return -1;
    int ok0 = header_valid(b0);
    int ok1 = header_valid(b1);
    if (!ok0 && !ok1) return -1;
    if (ok0 && !ok1) { *chosen_blk = 0; return 0; }
    if (!ok0 && ok1) { *chosen_blk = 1; return 0; }
    const kvfs_super_t *s0 = (const kvfs_super_t *)b0;
    const kvfs_super_t *s1 = (const kvfs_super_t *)b1;
    if (header_prefer_epoch()) {
        if (s0->epoch != s1->epoch) {
            *chosen_blk = s0->epoch > s1->epoch ? 0 : 1;
            return 0;
        }
        *chosen_blk = s0->durable_tx >= s1->durable_tx ? 0 : 1;
        return 0;
    }
    if (s0->durable_tx != s1->durable_tx) {
        *chosen_blk = s0->durable_tx >= s1->durable_tx ? 0 : 1;
        return 0;
    }
    if (s0->epoch != s1->epoch) {
        *chosen_blk = s0->epoch > s1->epoch ? 0 : 1;
        return 0;
    }
    *chosen_blk = 0;
    return 0;
}
