#ifndef SLOT_API_H
#define SLOT_API_H

#include <stdint.h>

int slot_open(void);
int slot_close(void);
int slot_abi_version(void);
int slot_frame_size(void);

#endif
