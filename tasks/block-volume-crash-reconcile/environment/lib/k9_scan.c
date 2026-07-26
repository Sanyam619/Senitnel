#include "kvfs_api.h"
#include "kvfs_layout.h"

#include <stdint.h>
#include <string.h>

#include "kvfs_internal.h"

int step_a_scan_redo(kvfs_volume *vol, uint64_t *tx_count) {
    if (!vol || !tx_count) return -1;
    uint64_t sealed = 0;
    size_t base = (size_t)KVFS_JOURNAL_BLK * KVFS_BLOCK_SIZE;
    size_t end = base + (size_t)KVFS_JOURNAL_BLKS * KVFS_BLOCK_SIZE;
    size_t pos = base;
    while (pos + 3 < end) {
        uint8_t tag = vol->map[pos];
        if (tag == KVFS_TAG_PAD || tag == 0) break;
        uint16_t body_len;
        memcpy(&body_len, vol->map + pos + 1, 2);
        pos += 3 + body_len;
        if (tag == KVFS_TAG_TX_SEAL) sealed++;
    }
    *tx_count = sealed;
    return 0;
}
