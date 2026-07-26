#ifndef HOST_H
#define HOST_H
#include "common.h"
int load_scenario(const char *path, struct scenario_in *out);
int load_profile(const char *path, struct profile_view *out);
int load_rebind(const char *path, struct rebind_view *out);
int load_floor(const char *path, struct floor_view *out);
int read_registry_epoch(const char *path, uint32_t *epoch);
void outcome_label(int outcome_kind, char *out, size_t n);
void category_label(const struct gate_slot *g, int polymorphic, char *out, size_t n);
int emit_report(const char *path, const struct case_out *cases, int n, uint32_t epoch);
#endif
