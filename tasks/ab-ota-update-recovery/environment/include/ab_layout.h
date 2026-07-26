#ifndef AB_LAYOUT_H
#define AB_LAYOUT_H

#include <stddef.h>
#include <stdint.h>

#define AB_SECTOR_SIZE 4096
#define AB_TOTAL_SECTORS 64
#define AB_IMAGE_BYTES (AB_SECTOR_SIZE * AB_TOTAL_SECTORS)
#define AB_PAYLOAD_SECTORS 16
#define AB_TREE_NODES 15

#define AB_SLOT_A_MAGIC "SLTA"
#define AB_SLOT_B_MAGIC "SLTB"
#define AB_BOOT_MAGIC "ABLD"
#define AB_LAYOUT_VERSION 1
#define AB_GUARD_WORD 0xA5A5A5A5U
#define AB_NO_PENDING 0xFFU

#define AB_PHASE_EMPTY 0
#define AB_PHASE_LIVE 1
#define AB_PHASE_STAGING 2
#define AB_PHASE_RETIRED 3

#define AB_SWAP_IDLE 0
#define AB_SWAP_ARMED 1
#define AB_SWAP_COMMIT 2

#define AB_HDR_A0_SEC 0
#define AB_HDR_A1_SEC 1
#define AB_HDR_B0_SEC 2
#define AB_HDR_B1_SEC 3
#define AB_BL0_SEC 4
#define AB_BL1_SEC 5
#define AB_PAYLOAD_A_SEC 6
#define AB_PAYLOAD_B_SEC 22
#define AB_TREE_A_SEC 38
#define AB_TREE_B_SEC 42

#pragma pack(push, 1)
typedef struct {
    char magic[4];
    uint32_t version;
    uint32_t boot_count;
    uint8_t boot_ok;
    uint8_t phase;
    uint8_t pad0[2];
    uint64_t generation;
    uint32_t payload_bytes;
    uint8_t root_hash[32];
    uint32_t hdr_crc32;
    uint8_t pad1[64];
} slot_hdr_t;

typedef struct {
    char magic[4];
    uint32_t version;
    uint8_t live_idx;
    uint8_t pending_idx;
    uint8_t swap_phase;
    uint8_t pad0;
    uint64_t commit_gen;
    uint32_t guard;
    uint32_t bl_crc32;
    uint8_t pad1[100];
} boot_ldr_t;
#pragma pack(pop)

#endif
