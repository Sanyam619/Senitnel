#ifndef IOCTL_A_H
#define IOCTL_A_H

#include <stddef.h>
#include <stdint.h>

int op_q(const uint8_t *a, size_t an, const uint8_t *b, size_t bn,
         uint32_t e, uint32_t f, uint8_t *out, size_t *outn);

#endif
