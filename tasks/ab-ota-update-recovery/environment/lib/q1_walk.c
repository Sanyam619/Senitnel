#include "ab_api.h"
#include "ab_layout.h"

#include <openssl/evp.h>
#include <string.h>

static void digest(const uint8_t *data, size_t len, uint8_t out[32]) {
    unsigned char buf[EVP_MAX_MD_SIZE];
    unsigned int dlen = 0;
    EVP_MD_CTX *ctx = EVP_MD_CTX_new();
    EVP_DigestInit_ex(ctx, EVP_sha256(), NULL);
    EVP_DigestUpdate(ctx, data, len);
    EVP_DigestFinal_ex(ctx, buf, &dlen);
    EVP_MD_CTX_free(ctx);
    memcpy(out, buf, 32);
}

int q1_walk_digest(const uint8_t *img, int slot_idx, int *ok) {
    if (!img || !ok) return -1;
    size_t base = (size_t)(slot_idx == 0 ? AB_PAYLOAD_A_SEC : AB_PAYLOAD_B_SEC) * AB_SECTOR_SIZE;
    size_t tree_base = (size_t)(slot_idx == 0 ? AB_TREE_A_SEC : AB_TREE_B_SEC) * AB_SECTOR_SIZE;
    uint8_t leaves[AB_PAYLOAD_SECTORS][32];
    for (int i = 0; i < AB_PAYLOAD_SECTORS; i++) {
        digest(img + base + (size_t)i * AB_SECTOR_SIZE, AB_SECTOR_SIZE, leaves[i]);
    }
    const uint8_t *stored = img + tree_base;
  int idx = 0;
    uint8_t level[AB_PAYLOAD_SECTORS][32];
    int count = AB_PAYLOAD_SECTORS;
    memcpy(level, leaves, sizeof(leaves));
    while (count > 1) {
        int next = 0;
        for (int i = 0; i < count; i += 2) {
            uint8_t pair[64];
            memcpy(pair, level[i], 32);
            if (i + 1 < count) memcpy(pair + 32, level[i + 1], 32);
            else memcpy(pair + 32, level[i], 32);
            digest(pair, 64, level[next]);
            if (idx < AB_TREE_NODES && memcmp(level[next], stored + (size_t)idx * 32, 32) != 0) {
                *ok = 0;
                return 0;
            }
            idx++;
            next++;
        }
        count = next;
    }
    size_t hdr_sec = (size_t)(slot_idx == 0 ? AB_HDR_A0_SEC : AB_HDR_B0_SEC);
    const slot_hdr_t *hdr = (const slot_hdr_t *)(img + hdr_sec * AB_SECTOR_SIZE);
    *ok = memcmp(level[0], hdr->root_hash, 32) == 0;
    return 0;
}
