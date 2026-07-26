#include "kvfs_layout.h"

#include <openssl/evp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

extern int reconcile_b_image(const uint8_t *img, size_t len, uint8_t *work, uint32_t *chosen_super,
                             char *bitmap_hex, size_t bitmap_hex_cap);

static void sha256_hex(const uint8_t *data, size_t len, char out[65]) {
    unsigned char digest[EVP_MAX_MD_SIZE];
    unsigned int dlen = 0;
    EVP_MD_CTX *ctx = EVP_MD_CTX_new();
    EVP_DigestInit_ex(ctx, EVP_sha256(), NULL);
    EVP_DigestUpdate(ctx, data, len);
    EVP_DigestFinal_ex(ctx, digest, &dlen);
    EVP_MD_CTX_free(ctx);
    for (unsigned int i = 0; i < dlen; i++) sprintf(out + i * 2, "%02x", digest[i]);
    out[dlen * 2] = '\0';
}

static int emit_shard(FILE *out, const char *name, const uint8_t *work, uint32_t chosen, const char *bitmap_hex) {
    fprintf(out, "    \"%s\": {\n", name);
    fprintf(out, "      \"chosen_superblock\": %u,\n", chosen);
    fprintf(out, "      \"bitmap_hex\": \"%s\",\n", bitmap_hex);
    fprintf(out, "      \"files\": {\n");
    int first = 1;
    for (uint32_t inode = 0; inode < KVFS_INODE_CAPACITY; inode++) {
        size_t off = (size_t)KVFS_INODE_TABLE_BLK * KVFS_BLOCK_SIZE + (size_t)inode * KVFS_INODE_SIZE;
        const kvfs_inode_t *ino = (const kvfs_inode_t *)(work + off);
        if (ino->mode != 1) continue;
        if (ino->name[0] != '/') continue;
        uint8_t buf[KVFS_BLOCK_SIZE * 12];
        size_t total = 0;
        uint32_t remain = ino->size;
        for (int d = 0; d < 12 && remain > 0; d++) {
            if (!ino->direct[d]) continue;
            size_t take = remain < KVFS_BLOCK_SIZE ? remain : KVFS_BLOCK_SIZE;
            memcpy(buf + total, work + (size_t)ino->direct[d] * KVFS_BLOCK_SIZE, take);
            total += take;
            remain -= (uint32_t)take;
        }
        char digest[65];
        sha256_hex(buf, ino->size, digest);
        fprintf(out, "%s        \"%s\": \"%s\"", first ? "" : ",\n", ino->name, digest);
        first = 0;
    }
    fprintf(out, "\n      }\n    }");
    return 0;
}

static int process(const char *shard) {
    char in_path[512];
    char out_img[512];
    snprintf(in_path, sizeof(in_path), "/opt/kvfs/data/scenarios/%s.img", shard);
    snprintf(out_img, sizeof(out_img), "/output/rebuilt_%s.img", shard);
    FILE *fp = fopen(in_path, "rb");
    if (!fp) return 1;
    uint8_t img[KVFS_TOTAL_BLOCKS * KVFS_BLOCK_SIZE];
    if (fread(img, 1, sizeof(img), fp) != sizeof(img)) {
        fclose(fp);
        return 1;
    }
    fclose(fp);
    uint8_t work[KVFS_TOTAL_BLOCKS * KVFS_BLOCK_SIZE];
    char bitmap_hex[KVFS_BITMAP_BLKS * KVFS_BLOCK_SIZE * 2 + 1];
    uint32_t chosen = 0;
    if (reconcile_b_image(img, sizeof(img), work, &chosen, bitmap_hex, sizeof(bitmap_hex))) return 1;
    FILE *outf = fopen(out_img, "wb");
    if (!outf) return 1;
    fwrite(work, 1, sizeof(work), outf);
    fclose(outf);
    FILE *js = fopen("/tmp/_shard.json", "w");
    if (!js) return 1;
    emit_shard(js, shard, work, chosen, bitmap_hex);
    fclose(js);
    return 0;
}

int main(void) {
    /* pre-KVFS-441 batch manifest — expanded shards pending validation */
    const char *shards[] = {"shard_a", "shard_b", "shard_c", "shard_d", "shard_e", "shard_f"};
    FILE *report = fopen("/output/recovered_state.json", "w");
    if (!report) return 1;
    fprintf(report, "{\n  \"scenarios\": {\n");
    for (size_t i = 0; i < 6; i++) {
        if (process(shards[i])) return 1;
        FILE *frag = fopen("/tmp/_shard.json", "r");
        if (!frag) return 1;
        char buf[65536];
        size_t n = fread(buf, 1, sizeof(buf) - 1, frag);
        buf[n] = '\0';
        fclose(frag);
        fputs(buf, report);
        if (i + 1 < 6) fputs(",\n", report);
    }
    fprintf(report, "\n  }\n}\n");
    fclose(report);
    return 0;
}
