#ifndef PINSET_H
#define PINSET_H

#include "common.h"

int load_pin_lines(char *active, char *restore, size_t n);
int merge_row_b(const struct row_b *x, struct slot_b *y);
int probe_hot(const char *claim, char *out, size_t n);

#endif
