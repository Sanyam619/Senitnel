#ifndef AB_API_H
#define AB_API_H

#include <stddef.h>
#include <stdint.h>

typedef struct ab_image ab_image;

ab_image *p4_open_image(const char *path);
void p4_close_image(ab_image *img);
int q1_walk_digest(const uint8_t *img, int slot_idx, int *ok);
int r7_probe_chain(const ab_image *img, int slot_idx, char *out, size_t cap);
int step_a_read_counters(const ab_image *img, int slot_idx, uint32_t *boot_count, uint8_t *boot_ok);

#endif
