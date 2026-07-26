#ifndef GATE_H
#define GATE_H

#include "common.h"

int slot_write_a(const char *id, const struct slot_a *s);
int slot_write_b(const char *id, const struct slot_b *s);
int slot_write_c(const char *id, const struct slot_c *s);
int slot_read_a(const char *id, struct slot_a *s);
int slot_read_b(const char *id, struct slot_b *s);
int slot_read_c(const char *id, struct slot_c *s);

int assemble_x(const struct case_in *in, struct case_out *out);
int assemble_y(const struct case_in *in, struct case_out *out);

#endif
