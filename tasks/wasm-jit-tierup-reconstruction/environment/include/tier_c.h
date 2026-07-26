#ifndef TIER_C_H
#define TIER_C_H
#include "common.h"
/* Admit/hold/refuse decision across profile + rebind + floor + heat. */
int fold_gate(const struct scenario_in *sc,
              const struct profile_slot *prof,
              const struct rebind_slot *rb,
              const struct floor_view *floor,
              uint32_t decision_epoch,
              struct gate_slot *out);
#endif
