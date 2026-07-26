#ifndef TIER_B_H
#define TIER_B_H
#include "common.h"
/* Fold a rebind authority journal row into the live signature slot. */
int fold_rebind(const struct rebind_view *in, struct rebind_slot *out);
#endif
