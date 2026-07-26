#include "ab_layout.h"
#include "ab_policy.h"

#include <stddef.h>
#include <openssl/evp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <zlib.h>

typedef struct {
    uint8_t phase;
    uint8_t boot_ok;
    uint32_t boot_count;
    uint64_t generation;
    uint32_t payload_bytes;
    uint8_t root_hash[32];
    int verity_ok;
} slot_view_t;

static uint32_t crc32_bytes(const void *data, size_t len) {
    return (uint32_t)crc32(0, (const unsigned char *)data, (unsigned int)len);
}

static void sha256_bytes(const uint8_t *data, size_t len, uint8_t out[32]) {
    unsigned char digest[EVP_MAX_MD_SIZE];
    unsigned int dlen = 0;
    EVP_MD_CTX *ctx = EVP_MD_CTX_new();
    EVP_DigestInit_ex(ctx, EVP_sha256(), NULL);
    EVP_DigestUpdate(ctx, data, len);
    EVP_DigestFinal_ex(ctx, digest, &dlen);
    EVP_MD_CTX_free(ctx);
    memcpy(out, digest, 32);
}

static int hdr_crc_ok(const slot_hdr_t *hdr) {
    const uint8_t *raw = (const uint8_t *)hdr;
    uint32_t got = crc32_bytes(raw, offsetof(slot_hdr_t, hdr_crc32));
    return got == hdr->hdr_crc32;
}

static int bl_crc_ok(const boot_ldr_t *bl) {
    const uint8_t *raw = (const uint8_t *)bl;
    uint32_t got = crc32_bytes(raw, offsetof(boot_ldr_t, bl_crc32));
    return got == bl->bl_crc32 && bl->guard == AB_GUARD_WORD;
}

static int read_hdr_mirror(const uint8_t *img, int slot, int mirror, slot_hdr_t *out) {
    size_t sec = (size_t)(slot == 0 ? (mirror == 0 ? AB_HDR_A0_SEC : AB_HDR_A1_SEC)
                                     : (mirror == 0 ? AB_HDR_B0_SEC : AB_HDR_B1_SEC));
    memcpy(out, img + sec * AB_SECTOR_SIZE, sizeof(*out));
    return hdr_crc_ok(out);
}

static int pick_hdr(const uint8_t *img, int slot, slot_hdr_t *chosen) {
    slot_hdr_t m0, m1;
    int ok0 = read_hdr_mirror(img, slot, 0, &m0);
    int ok1 = read_hdr_mirror(img, slot, 1, &m1);
    if (!ok0 && !ok1) return -1;
    if (ok0 && !ok1) {
        *chosen = m0;
        return 0;
    }
    if (!ok0 && ok1) {
        *chosen = m1;
        return 0;
    }
    *chosen = m0.generation >= m1.generation ? m0 : m1;
    return 0;
}

static int verify_chain(const uint8_t *img, int slot, const slot_hdr_t *hdr, int *ok) {
    size_t base = (size_t)(slot == 0 ? AB_PAYLOAD_A_SEC : AB_PAYLOAD_B_SEC) * AB_SECTOR_SIZE;
    size_t tree_base = (size_t)(slot == 0 ? AB_TREE_A_SEC : AB_TREE_B_SEC) * AB_SECTOR_SIZE;
    uint8_t leaves[AB_PAYLOAD_SECTORS][32];
    for (int i = 0; i < AB_PAYLOAD_SECTORS; i++) {
        sha256_bytes(img + base + (size_t)i * AB_SECTOR_SIZE, AB_SECTOR_SIZE, leaves[i]);
    }
    uint8_t level[AB_PAYLOAD_SECTORS][32];
    int count = AB_PAYLOAD_SECTORS;
    memcpy(level, leaves, sizeof(leaves));
    const uint8_t *stored = img + tree_base;
    int stored_idx = 0;
    while (count > 1) {
        int next = 0;
        for (int i = 0; i < count; i += 2) {
            uint8_t pair[64];
            memcpy(pair, level[i], 32);
            if (i + 1 < count) {
                memcpy(pair + 32, level[i + 1], 32);
            } else {
                memcpy(pair + 32, level[i], 32);
            }
            sha256_bytes(pair, 64, level[next]);
            if (stored_idx < AB_TREE_NODES) {
                if (memcmp(level[next], stored + (size_t)stored_idx * 32, 32) != 0) {
                    *ok = 0;
                    return 0;
                }
                stored_idx++;
            }
            next++;
        }
        count = next;
    }
    *ok = memcmp(level[0], hdr->root_hash, 32) == 0;
    return 0;
}

static void fill_view(const uint8_t *img, int slot, slot_view_t *view) {
    slot_hdr_t hdr;
    memset(view, 0, sizeof(*view));
    if (pick_hdr(img, slot, &hdr)) return;
    view->phase = hdr.phase;
    view->boot_ok = hdr.boot_ok;
    view->boot_count = hdr.boot_count;
    view->generation = hdr.generation;
    view->payload_bytes = hdr.payload_bytes;
    memcpy(view->root_hash, hdr.root_hash, 32);
    int ok = 0;
    verify_chain(img, slot, &hdr, &ok);
    view->verity_ok = ok;
}

static void write_hdr(uint8_t *img, int slot, int mirror, const slot_hdr_t *hdr) {
    size_t sec = (size_t)(slot == 0 ? (mirror == 0 ? AB_HDR_A0_SEC : AB_HDR_A1_SEC)
                                     : (mirror == 0 ? AB_HDR_B0_SEC : AB_HDR_B1_SEC));
    memcpy(img + sec * AB_SECTOR_SIZE, hdr, sizeof(*hdr));
}

static void write_bl(uint8_t *img, int mirror, const boot_ldr_t *bl) {
    size_t sec = (size_t)(mirror == 0 ? AB_BL0_SEC : AB_BL1_SEC);
    memcpy(img + sec * AB_SECTOR_SIZE, bl, sizeof(*bl));
}

static void pack_hdr(slot_hdr_t *hdr, int slot, uint8_t phase, uint8_t boot_ok, uint32_t boot_count,
                     uint64_t generation, uint32_t payload_bytes, const uint8_t root[32]) {
    memset(hdr, 0, sizeof(*hdr));
    memcpy(hdr->magic, slot == 0 ? AB_SLOT_A_MAGIC : AB_SLOT_B_MAGIC, 4);
    hdr->version = AB_LAYOUT_VERSION;
    hdr->boot_count = boot_count;
    hdr->boot_ok = boot_ok;
    hdr->phase = phase;
    hdr->generation = generation;
    hdr->payload_bytes = payload_bytes;
    memcpy(hdr->root_hash, root, 32);
    hdr->hdr_crc32 = crc32_bytes(hdr, offsetof(slot_hdr_t, hdr_crc32));
}

static void pack_bl(boot_ldr_t *bl, uint8_t live_idx, uint8_t pending_idx, uint8_t swap_phase,
                    uint64_t commit_gen) {
    memset(bl, 0, sizeof(*bl));
    memcpy(bl->magic, AB_BOOT_MAGIC, 4);
    bl->version = AB_LAYOUT_VERSION;
    bl->live_idx = live_idx;
    bl->pending_idx = pending_idx;
    bl->swap_phase = swap_phase;
    bl->commit_gen = commit_gen;
    bl->guard = AB_GUARD_WORD;
    bl->bl_crc32 = crc32_bytes(bl, offsetof(boot_ldr_t, bl_crc32));
}

static int rule_matches(ab_rule_id_t rule, int pending, int live, slot_view_t *va, slot_view_t *vb,
                        int a_live, int b_live, int a_ok, int b_ok, int allow_commit) {
    switch (rule) {
    case AB_RULE_ROLLBACK_STAGING_B:
        return pending == 1 && vb->phase == AB_PHASE_STAGING && !vb->verity_ok;
    case AB_RULE_REPOINT_LIVE_B_FAIL:
        return live == 1 && !vb->verity_ok && a_live;
    case AB_RULE_COMMIT_STAGING_A:
        return allow_commit && pending == 0 && va->phase == AB_PHASE_STAGING && va->verity_ok && !b_ok;
    case AB_RULE_ROLLBACK_LIVE_B_FAIL:
        return pending == 1 && !vb->verity_ok && a_live;
    case AB_RULE_HOLD:
        return 1;
    default:
        return 0;
    }
}

static void apply_rule(ab_rule_id_t rule, int *live, int *pending, slot_view_t *va, slot_view_t *vb,
                       int a_live, int a_ok, const char **act) {
    switch (rule) {
    case AB_RULE_ROLLBACK_STAGING_B:
        *act = "rollback";
        *live = a_live ? 0 : (a_ok ? 0 : *live);
        vb->phase = AB_PHASE_RETIRED;
        *pending = -1;
        break;
    case AB_RULE_REPOINT_LIVE_B_FAIL:
        *act = "repoint";
        *live = 0;
        vb->phase = AB_PHASE_RETIRED;
        *pending = -1;
        break;
    case AB_RULE_COMMIT_STAGING_A:
        *act = "commit";
        va->phase = AB_PHASE_LIVE;
        va->boot_ok = 1;
        vb->phase = AB_PHASE_RETIRED;
        *live = 0;
        *pending = -1;
        break;
    case AB_RULE_ROLLBACK_LIVE_B_FAIL:
        *act = "rollback";
        vb->phase = AB_PHASE_RETIRED;
        *pending = -1;
        *live = 0;
        break;
    case AB_RULE_HOLD:
    default:
        *act = "hold";
        break;
    }
}

int m3_finalize_region(const uint8_t *img, size_t len, uint8_t *work, int *live_slot,
                       char *action, size_t action_cap, int *bootable_a, int *bootable_b,
                       const ab_recovery_policy_t *policy_in) {
    ab_recovery_policy_t policy_local;
    const ab_recovery_policy_t *policy = policy_in;
    if (!policy) {
        if (ab_policy_default(&policy_local)) return -1;
        policy = &policy_local;
    }
    if (len < AB_IMAGE_BYTES) return -1;
    memcpy(work, img, AB_IMAGE_BYTES);

    slot_view_t va, vb;
    fill_view(img, 0, &va);
    fill_view(img, 1, &vb);

    boot_ldr_t bl0, bl1;
    memcpy(&bl0, img + AB_BL0_SEC * AB_SECTOR_SIZE, sizeof(bl0));
    memcpy(&bl1, img + AB_BL1_SEC * AB_SECTOR_SIZE, sizeof(bl1));
    boot_ldr_t cur = bl_crc_ok(&bl0) ? bl0 : bl1;
    if (!bl_crc_ok(&bl0) && !bl_crc_ok(&bl1)) return -1;

    int live = (int)cur.live_idx;
    int pending = cur.pending_idx == AB_NO_PENDING ? -1 : (int)cur.pending_idx;

    int a_live = va.phase == AB_PHASE_LIVE && va.verity_ok;
    int b_live = vb.phase == AB_PHASE_LIVE && vb.verity_ok;
    int a_ok = va.verity_ok && va.phase != AB_PHASE_RETIRED;
    int b_ok = vb.verity_ok && vb.phase != AB_PHASE_RETIRED;

    if (!(a_live || b_live || (va.verity_ok && va.phase == AB_PHASE_STAGING) ||
          (vb.verity_ok && vb.phase == AB_PHASE_STAGING))) {
        return -1;
    }

    const char *act = "hold";
    for (int i = 0; i < policy->rule_count; i++) {
        ab_rule_id_t rule = policy->rule_order[i];
        if (rule_matches(rule, pending, live, &va, &vb, a_live, b_live, a_ok, b_ok,
                         policy->allow_commit)) {
            apply_rule(rule, &live, &pending, &va, &vb, a_live, a_ok, &act);
            break;
        }
    }

    slot_hdr_t ha, hb;
    pick_hdr(work, 0, &ha);
    pick_hdr(work, 1, &hb);
    pack_hdr(&ha, 0, va.phase, va.boot_ok, va.boot_count, va.generation, va.payload_bytes, va.root_hash);
    pack_hdr(&hb, 1, vb.phase, vb.boot_ok, vb.boot_count, vb.generation, vb.payload_bytes, vb.root_hash);
    write_hdr(work, 0, 0, &ha);
    write_hdr(work, 0, 1, &ha);
    write_hdr(work, 1, 0, &hb);
    write_hdr(work, 1, 1, &hb);

    boot_ldr_t out;
    pack_bl(&out, (uint8_t)live, pending < 0 ? AB_NO_PENDING : (uint8_t)pending, AB_SWAP_IDLE,
            cur.commit_gen + 1);
    write_bl(work, 0, &out);
    write_bl(work, 1, &out);

    *live_slot = live;
    snprintf(action, action_cap, "%s", act);
    *bootable_a = (va.phase == AB_PHASE_LIVE && va.verity_ok) ? 1 : 0;
    *bootable_b = (vb.phase == AB_PHASE_LIVE && vb.verity_ok) ? 1 : 0;
    return 0;
}
