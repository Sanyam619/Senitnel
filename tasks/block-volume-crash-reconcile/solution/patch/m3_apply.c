#include "kvfs_layout.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <zlib.h>

#define POLICY_PATH "/opt/kvfs/config/recovery_policy.ini"

typedef struct {
    int replay_tx_id_order;
    int forget_invalidate_earlier;
    uint32_t metadata_used_end;
    int patch_zero_pad;
    int preserve_superblocks;
    int header_prefer_epoch;
} recovery_policy_t;

typedef struct {
    uint64_t tx_id;
    uint32_t block;
    uint8_t *payload;
    size_t payload_len;
} patch_t;

typedef struct {
    uint64_t tx_id;
    uint32_t *blocks;
    size_t n_blocks;
} forget_t;

static void load_policy(recovery_policy_t *pol) {
    pol->replay_tx_id_order = 1;
    pol->forget_invalidate_earlier = 1;
    pol->metadata_used_end = 28;
    pol->patch_zero_pad = 1;
    pol->preserve_superblocks = 1;
    pol->header_prefer_epoch = 1;

    FILE *fp = fopen(POLICY_PATH, "r");
    if (!fp) return;
    char line[256];
    while (fgets(line, sizeof(line), fp)) {
        char key[64], val[64];
        if (sscanf(line, " %63[^=] = %63s", key, val) != 2) continue;
        if (strcmp(key, "order") == 0 && strcmp(val, "tx_id") == 0) pol->replay_tx_id_order = 1;
        if (strcmp(key, "order") == 0 && strcmp(val, "journal") == 0) pol->replay_tx_id_order = 0;
        if (strcmp(key, "forget_mode") == 0 && strcmp(val, "invalidate_earlier") == 0)
            pol->forget_invalidate_earlier = 1;
        if (strcmp(key, "forget_mode") == 0 && strcmp(val, "forward") == 0)
            pol->forget_invalidate_earlier = 0;
        if (strcmp(key, "metadata_used_end") == 0) pol->metadata_used_end = (uint32_t)strtoul(val, NULL, 10);
        if (strcmp(key, "patch_zero_pad") == 0) pol->patch_zero_pad = (strcmp(val, "1") == 0 || strcmp(val, "true") == 0);
        if (strcmp(key, "preserve_superblocks") == 0)
            pol->preserve_superblocks = (strcmp(val, "1") == 0 || strcmp(val, "true") == 0);
        if (strcmp(key, "prefer") == 0 && strcmp(val, "durable_tx") == 0) pol->header_prefer_epoch = 0;
        if (strcmp(key, "prefer") == 0 && strcmp(val, "epoch") == 0) pol->header_prefer_epoch = 1;
    }
    fclose(fp);
}

static uint32_t crc32_bytes(const void *data, size_t len) {
    return (uint32_t)crc32(0, (const unsigned char *)data, (unsigned int)len);
}

static int header_valid(const uint8_t *blk, uint32_t *epoch, uint32_t *durable_tx) {
    const kvfs_super_t *sb = (const kvfs_super_t *)blk;
    if (memcmp(sb->magic, KVFS_MAGIC, 4) != 0) return 0;
    if (crc32_bytes(blk, 68) != sb->sb_crc32) return 0;
    if (sb->primary_ok != 1) return 0;
    *epoch = (uint32_t)sb->epoch;
    *durable_tx = (uint32_t)sb->durable_tx;
    return 1;
}

static uint32_t pick_super(const uint8_t *img, const recovery_policy_t *pol) {
    uint32_t e0 = 0, d0 = 0, e1 = 0, d1 = 0;
    int v0 = header_valid(img, &e0, &d0);
    int v1 = header_valid(img + KVFS_BLOCK_SIZE, &e1, &d1);
    if (v0 && !v1) return 0;
    if (!v0 && v1) return 1;
    if (!v0 && !v1) return 0;
    if (pol->header_prefer_epoch) {
        if (e0 != e1) return e0 > e1 ? 0 : 1;
        return d0 >= d1 ? 0 : 1;
    }
    if (d0 != d1) return d0 >= d1 ? 0 : 1;
    if (e0 != e1) return e0 > e1 ? 0 : 1;
    return 0;
}

static void apply_patch(uint8_t *work, uint32_t blk, const uint8_t *payload, size_t len, const recovery_policy_t *pol) {
    uint8_t *dst = work + (size_t)blk * KVFS_BLOCK_SIZE;
    size_t n = len < KVFS_BLOCK_SIZE ? len : KVFS_BLOCK_SIZE;
    memcpy(dst, payload, n);
    if (pol->patch_zero_pad && n < KVFS_BLOCK_SIZE) memset(dst + n, 0, KVFS_BLOCK_SIZE - n);
}

static int scan_journal(const uint8_t *img, patch_t **patches, size_t *n_patches,
                        forget_t **forgets, size_t *n_forgets, uint64_t **sealed, size_t *n_sealed) {
    size_t base = (size_t)KVFS_JOURNAL_BLK * KVFS_BLOCK_SIZE;
    size_t end = base + (size_t)KVFS_JOURNAL_BLKS * KVFS_BLOCK_SIZE;
    size_t pos = base;
    uint64_t open_tx = 0;
    int have_open = 0;
    *patches = NULL;
    *n_patches = 0;
    *forgets = NULL;
    *n_forgets = 0;
    *sealed = NULL;
    *n_sealed = 0;

    while (pos + 3 < end) {
        uint8_t tag = img[pos];
        if (tag == KVFS_TAG_PAD || tag == 0) break;
        uint16_t body_len;
        memcpy(&body_len, img + pos + 1, 2);
        const uint8_t *body = img + pos + 3;
        pos += 3 + body_len;
        if (tag == KVFS_TAG_TX_OPEN) {
            memcpy(&open_tx, body, 8);
            have_open = 1;
        } else if (tag == KVFS_TAG_BLK_PATCH && have_open) {
            uint32_t blk;
            memcpy(&blk, body, 4);
            patch_t p = {.tx_id = open_tx, .block = blk, .payload = (uint8_t *)(body + 4), .payload_len = body_len - 4};
            patch_t *np = realloc(*patches, (*n_patches + 1) * sizeof(patch_t));
            if (!np) return -1;
            *patches = np;
            (*patches)[*n_patches] = p;
            (*n_patches)++;
        } else if (tag == KVFS_TAG_TX_SEAL) {
            uint64_t tx;
            memcpy(&tx, body, 8);
            uint64_t *ns = realloc(*sealed, (*n_sealed + 1) * sizeof(uint64_t));
            if (!ns) return -1;
            *sealed = ns;
            (*sealed)[*n_sealed] = tx;
            (*n_sealed)++;
            have_open = 0;
        } else if (tag == KVFS_TAG_BLK_FORGET) {
            uint64_t tx;
            uint16_t n;
            memcpy(&tx, body, 8);
            memcpy(&n, body + 8, 2);
            forget_t f = {.tx_id = tx, .n_blocks = n, .blocks = malloc((size_t)n * sizeof(uint32_t))};
            if (!f.blocks) return -1;
            memcpy(f.blocks, body + 10, (size_t)n * 4);
            forget_t *nf = realloc(*forgets, (*n_forgets + 1) * sizeof(forget_t));
            if (!nf) return -1;
            *forgets = nf;
            (*forgets)[*n_forgets] = f;
            (*n_forgets)++;
        }
    }
    return 0;
}

static int is_sealed(uint64_t tx, uint64_t *sealed, size_t n_sealed) {
    for (size_t i = 0; i < n_sealed; i++) if (sealed[i] == tx) return 1;
    return 0;
}

static uint64_t forget_level(uint32_t blk, forget_t *forgets, size_t n_forgets, uint64_t *sealed, size_t n_sealed) {
    uint64_t best = 0;
    for (size_t i = 0; i < n_forgets; i++) {
        if (!is_sealed(forgets[i].tx_id, sealed, n_sealed)) continue;
        for (size_t j = 0; j < forgets[i].n_blocks; j++) {
            if (forgets[i].blocks[j] == blk && forgets[i].tx_id > best) best = forgets[i].tx_id;
        }
    }
    return best;
}

static int cmp_u64(const void *a, const void *b) {
    uint64_t x = *(const uint64_t *)a;
    uint64_t y = *(const uint64_t *)b;
    if (x < y) return -1;
    if (x > y) return 1;
    return 0;
}

static int forget_blocks_patch(uint64_t fl, uint64_t tx, const recovery_policy_t *pol) {
    if (fl == 0) return 0;
    if (pol->forget_invalidate_earlier) return fl > tx;
    return tx <= fl;
}

int reconcile_b_image(const uint8_t *img, size_t len, uint8_t *work, uint32_t *chosen_super,
                      char *bitmap_hex, size_t bitmap_hex_cap) {
    if (len < (size_t)KVFS_TOTAL_BLOCKS * KVFS_BLOCK_SIZE) return -1;
    recovery_policy_t pol;
    load_policy(&pol);

    memcpy(work, img, (size_t)KVFS_TOTAL_BLOCKS * KVFS_BLOCK_SIZE);
    *chosen_super = pick_super(img, &pol);

    patch_t *patches = NULL;
    size_t n_patches = 0;
    forget_t *forgets = NULL;
    size_t n_forgets = 0;
    uint64_t *sealed = NULL;
    size_t n_sealed = 0;
    if (scan_journal(img, &patches, &n_patches, &forgets, &n_forgets, &sealed, &n_sealed)) return -1;

    if (pol.replay_tx_id_order)
        qsort(sealed, n_sealed, sizeof(uint64_t), cmp_u64);

    for (size_t s = 0; s < n_sealed; s++) {
        uint64_t tx = sealed[s];
        for (size_t i = 0; i < n_patches; i++) {
            if (patches[i].tx_id != tx) continue;
            uint64_t fl = forget_level(patches[i].block, forgets, n_forgets, sealed, n_sealed);
            if (forget_blocks_patch(fl, tx, &pol)) continue;
            apply_patch(work, patches[i].block, patches[i].payload, patches[i].payload_len, &pol);
        }
    }

    uint8_t bits[KVFS_BITMAP_BLKS * KVFS_BLOCK_SIZE];
    memset(bits, 0, sizeof(bits));
    for (uint32_t b = 0; b < pol.metadata_used_end && b < KVFS_TOTAL_BLOCKS; b++)
        bits[b / 8] |= (uint8_t)(1u << (b % 8));
    for (uint32_t inode = 0; inode < KVFS_INODE_CAPACITY; inode++) {
        size_t off = (size_t)KVFS_INODE_TABLE_BLK * KVFS_BLOCK_SIZE + (size_t)inode * KVFS_INODE_SIZE;
        const kvfs_inode_t *ino = (const kvfs_inode_t *)(work + off);
        if (ino->mode == 0) continue;
        for (int d = 0; d < 12; d++)
            if (ino->direct[d]) bits[ino->direct[d] / 8] |= (uint8_t)(1u << (ino->direct[d] % 8));
    }
    for (size_t i = 0; i < sizeof(bits); i++) {
        if ((size_t)(i * 2 + 1) >= bitmap_hex_cap) return -1;
        sprintf(bitmap_hex + i * 2, "%02x", bits[i]);
    }
    bitmap_hex[sizeof(bits) * 2] = '\0';
    memcpy(work + (size_t)KVFS_BITMAP_BLK * KVFS_BLOCK_SIZE, bits, sizeof(bits));

    if (pol.preserve_superblocks) {
        memcpy(work, img, (size_t)2 * KVFS_BLOCK_SIZE);
    }

    free(patches);
    for (size_t i = 0; i < n_forgets; i++) free(forgets[i].blocks);
    free(forgets);
    free(sealed);
    return 0;
}
