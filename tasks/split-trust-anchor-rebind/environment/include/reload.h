#ifndef RELOAD_H
#define RELOAD_H

#include <stdint.h>

int epoch_read(uint32_t *out);
int apply_snap(void);

#endif
