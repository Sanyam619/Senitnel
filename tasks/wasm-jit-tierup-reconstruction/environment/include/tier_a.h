#ifndef TIER_A_H
#define TIER_A_H
#include "common.h"
/* Fold a profile authority tape row into the durable probe slot. */
int fold_profile(const struct profile_view *in, struct profile_slot *out);
#endif
