/*
 * Verifier-owned reconciliation probe.
 *
 * This program is staged into a scratch build directory by tests/conftest.py
 * and compiled against the agent's live /opt/kvfs/lib/m3_apply.o and
 * /opt/kvfs/lib/libkvfs.a. It exercises reconcile_b_image() directly on a
 * crash image and prints the reconciled digest plus the chosen superblock
 * and bitmap. The verifier compares that output against precomputed digests,
 * so a fabricated /output/*.json or a hand-written /opt/kvfs/bin/reconcile
 * that hard-codes correct outputs cannot mask a broken library.
 */
#include "kvfs_layout.h"

#include <openssl/evp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int reconcile_b_image(const unsigned char *img, size_t len, unsigned char *work,
                      unsigned int *chosen_super, char *bitmap_hex, size_t cap);

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: verify_probe <image>\n");
        return 2;
    }
    FILE *fp = fopen(argv[1], "rb");
    if (!fp) { perror("open"); return 1; }
    size_t total = (size_t)KVFS_TOTAL_BLOCKS * KVFS_BLOCK_SIZE;
    unsigned char *img = malloc(total);
    unsigned char *work = malloc(total);
    if (!img || !work) { fclose(fp); return 3; }
    if (fread(img, 1, total, fp) != total) { fclose(fp); return 4; }
    fclose(fp);

    unsigned int chosen = 0;
    char bitmap_hex[KVFS_BITMAP_BLKS * KVFS_BLOCK_SIZE * 2 + 1];
    if (reconcile_b_image(img, total, work, &chosen, bitmap_hex,
                          sizeof(bitmap_hex))) {
        fprintf(stderr, "reconcile_b_image failed\n");
        return 5;
    }

    unsigned char digest[EVP_MAX_MD_SIZE];
    unsigned int dlen = 0;
    EVP_MD_CTX *ctx = EVP_MD_CTX_new();
    if (!ctx) return 6;
    EVP_DigestInit_ex(ctx, EVP_sha256(), NULL);
    EVP_DigestUpdate(ctx, work, total);
    EVP_DigestFinal_ex(ctx, digest, &dlen);
    EVP_MD_CTX_free(ctx);

    printf("chosen=%u\n", chosen);
    printf("bitmap=%s\n", bitmap_hex);
    printf("digest=");
    for (unsigned int i = 0; i < dlen; i++) printf("%02x", digest[i]);
    printf("\n");

    free(img);
    free(work);
    return 0;
}
