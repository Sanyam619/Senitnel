#ifndef KVFS_LAYOUT_H
#define KVFS_LAYOUT_H

#include <stdint.h>

#define KVFS_MAGIC "KVFS"
#define KVFS_VERSION 1
#define KVFS_BLOCK_SIZE 4096
#define KVFS_TOTAL_BLOCKS 256

#define KVFS_INODE_TABLE_BLK 2
#define KVFS_INODE_TABLE_BLKS 4
#define KVFS_INODE_CAPACITY 128
#define KVFS_INODE_SIZE 128

#define KVFS_BITMAP_BLK 6
#define KVFS_BITMAP_BLKS 2

#define KVFS_JOURNAL_BLK 8
#define KVFS_JOURNAL_BLKS 20

#define KVFS_DATA_START 28

#define KVFS_TAG_PAD 0x00
#define KVFS_TAG_TX_OPEN 0xA1
#define KVFS_TAG_BLK_PATCH 0xA2
#define KVFS_TAG_TX_SEAL 0xA3
#define KVFS_TAG_BLK_FORGET 0xA4

#pragma pack(push, 1)
typedef struct {
    char magic[4];
    uint32_t version;
    uint32_t block_size;
    uint32_t total_blocks;
    uint32_t inode_table_blk;
    uint32_t inode_table_blks;
    uint32_t inode_capacity;
    uint32_t bitmap_blk;
    uint32_t bitmap_blks;
    uint32_t journal_blk;
    uint32_t journal_blks;
    uint32_t data_start_blk;
    uint64_t epoch;
    uint64_t durable_tx;
    uint32_t primary_ok;
    uint32_t sb_crc32;
} kvfs_super_t;

typedef struct {
    uint16_t mode;
    uint16_t links;
    uint32_t size;
    uint32_t inode_id;
    char name[48];
    uint16_t direct[12];
    uint64_t mtime;
    uint8_t pad[24];
} kvfs_inode_t;
#pragma pack(pop)

#endif
