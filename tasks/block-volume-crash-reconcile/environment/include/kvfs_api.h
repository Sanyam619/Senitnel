#ifndef KVFS_API_H
#define KVFS_API_H

#include <stddef.h>
#include <stdint.h>

typedef struct kvfs_volume kvfs_volume;

kvfs_volume *op_open_vol(const char *path);
void op_close_vol(kvfs_volume *vol);
int op_read_block(kvfs_volume *vol, uint32_t blk, void *out, size_t len);
int step_a_scan_redo(kvfs_volume *vol, uint64_t *tx_count);
int resolve_c_pick_header(kvfs_volume *vol, uint32_t *chosen_blk);
int r2_walk_inodes(kvfs_volume *vol, void (*cb)(const char *name, uint32_t size, void *ctx), void *ctx);
uint32_t u8_crc32_bytes(const void *data, size_t len);

#endif
