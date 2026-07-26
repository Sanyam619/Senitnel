#include "ab_api.h"
#include "ab_layout.h"

#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <zlib.h>

#include "ab_internal.h"

static int bl_ok(const boot_ldr_t *bl) {
    uint32_t got = (uint32_t)crc32(0, (const unsigned char *)bl, offsetof(boot_ldr_t, bl_crc32));
    return got == bl->bl_crc32 && bl->guard == AB_GUARD_WORD;
}

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: bootsim <image>\n");
        return 2;
    }
    ab_image *img = p4_open_image(argv[1]);
    if (!img) { perror("open"); return 1; }
    const boot_ldr_t *b0 = (const boot_ldr_t *)(img->map + AB_BL0_SEC * AB_SECTOR_SIZE);
    const boot_ldr_t *b1 = (const boot_ldr_t *)(img->map + AB_BL1_SEC * AB_SECTOR_SIZE);
    const boot_ldr_t *bl = bl_ok(b0) ? b0 : (bl_ok(b1) ? b1 : NULL);
    if (!bl) { fprintf(stderr, "control record invalid\n"); p4_close_image(img); return 1; }
    int ok = 0;
    if (q1_walk_digest(img->map, (int)bl->live_idx, &ok) || !ok) {
        fprintf(stderr, "integrity failure on live copy\n");
        p4_close_image(img);
        return 1;
    }
    printf("live=%c verity=pass\n", bl->live_idx == 0 ? 'a' : 'b');
    p4_close_image(img);
    return 0;
}
