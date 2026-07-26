#ifndef KLB_FMT_H
#define KLB_FMT_H

#include "klb_types.h"

int klb_parse_trace(const char *path, KlbWeave *out);
int klb_load_set(const char *path, char actors[][32], int prios[], char gates[][32], int *n_act, int *n_gate);

#endif
