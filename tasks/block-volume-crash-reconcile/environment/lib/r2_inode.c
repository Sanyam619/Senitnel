#include "kvfs_api.h"
#include "kvfs_layout.h"

#include <string.h>

#include "kvfs_internal.h"

int r2_walk_inodes(kvfs_volume *vol, void (*cb)(const char *name, uint32_t size, void *ctx), void *ctx) {
    if (!vol || !cb) return -1;
    for (uint32_t i = 0; i < KVFS_INODE_CAPACITY; i++) {
        size_t off = (size_t)KVFS_INODE_TABLE_BLK * KVFS_BLOCK_SIZE + (size_t)i * KVFS_INODE_SIZE;
        if (off + KVFS_INODE_SIZE > vol->len) break;
        const kvfs_inode_t *ino = (const kvfs_inode_t *)(vol->map + off);
        if (ino->mode == 0) continue;
        cb(ino->name, ino->size, ctx);
    }
    return 0;
}
