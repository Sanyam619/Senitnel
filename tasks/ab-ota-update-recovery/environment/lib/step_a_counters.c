#include "ab_api.h"
#include "ab_layout.h"

#include <stddef.h>
#include <string.h>
#include <zlib.h>

#include "ab_internal.h"

static int hdr_ok(const slot_hdr_t *hdr) {
    uint32_t got = (uint32_t)crc32(0, (const unsigned char *)hdr, offsetof(slot_hdr_t, hdr_crc32));
    return got == hdr->hdr_crc32;
}

int step_a_read_counters(const ab_image *img, int slot_idx, uint32_t *boot_count, uint8_t *boot_ok) {
    if (!img || !boot_count || !boot_ok) return -1;
    size_t s0 = (size_t)(slot_idx == 0 ? AB_HDR_A0_SEC : AB_HDR_B0_SEC) * AB_SECTOR_SIZE;
    size_t s1 = (size_t)(slot_idx == 0 ? AB_HDR_A1_SEC : AB_HDR_B1_SEC) * AB_SECTOR_SIZE;
    const slot_hdr_t *h0 = (const slot_hdr_t *)(img->map + s0);
    const slot_hdr_t *h1 = (const slot_hdr_t *)(img->map + s1);
    const slot_hdr_t *pick = NULL;
    if (hdr_ok(h0) && !hdr_ok(h1)) pick = h0;
    else if (!hdr_ok(h0) && hdr_ok(h1)) pick = h1;
    else if (hdr_ok(h0) && hdr_ok(h1)) pick = h0->generation >= h1->generation ? h0 : h1;
  else return -1;
    *boot_count = pick->boot_count;
    *boot_ok = pick->boot_ok;
    return 0;
}
