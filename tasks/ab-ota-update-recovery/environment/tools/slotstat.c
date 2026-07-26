#include "ab_api.h"

#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: slotstat <image>\n");
        return 2;
    }
    ab_image *img = p4_open_image(argv[1]);
    if (!img) { perror("open"); return 1; }
    for (int slot = 0; slot < 2; slot++) {
        uint32_t boot_count = 0;
        uint8_t boot_ok = 0;
        if (step_a_read_counters(img, slot, &boot_count, &boot_ok)) {
            printf("slot=%c boot_count=invalid boot_ok=invalid\n", slot == 0 ? 'a' : 'b');
            continue;
        }
        printf("slot=%c boot_count=%u boot_ok=%u\n", slot == 0 ? 'a' : 'b', boot_count, boot_ok);
    }
    p4_close_image(img);
    return 0;
}
