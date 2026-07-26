#ifndef COMMON_H
#define COMMON_H

#include <stdint.h>
#include <stddef.h>

#define MAX_LINE 256
#define MAX_ID 32
#define MAX_KIND 16
#define MAX_CATEGORY 40
#define MAX_CASES 32
#define MAX_PATH 256

struct scenario_in {
    char id[MAX_ID];
    int32_t is_hot;
    int32_t is_very_hot;
    int32_t triggers_reload;
    int32_t attempts_host_call;
    int32_t host_is_legit;
    int32_t live_table;
};

/* Profile authority view (hot-path probe tape). */
struct profile_view {
    char id[MAX_ID];
    int32_t has_profile;
    int32_t polymorphic;
    int32_t probe_count;
    int32_t reload_seen;
    uint32_t epoch_stamp_raw;
    int32_t trust_mark; /* 1=claimed-trustworthy in tape; may be stale */
};

/* Rebind authority view (import signature journal). */
struct rebind_view {
    char id[MAX_ID];
    char old_type[MAX_KIND];
    char new_type[MAX_KIND];
    int32_t old_arity, new_arity;
    int32_t old_bounds, new_bounds;
    int32_t old_table, new_table;
    int32_t recorded; /* 1 if a rebind record exists for this id */
};

/* Floor bait view (surface policy hint — not decisive). */
struct floor_view {
    char id[MAX_ID];
    char hint_outcome[MAX_KIND];
    char hint_category[MAX_CATEGORY];
    int32_t hint_host;
};

struct profile_slot {
    int32_t has_profile;
    int32_t trustworthy;
    int32_t polymorphic;
    uint32_t epoch_stamp;
};

struct rebind_slot {
    int32_t signature_changed;
    int32_t change_type;
    int32_t change_arity;
    int32_t change_bounds;
    int32_t change_table;
};

struct gate_slot {
    int32_t promote;
    int32_t outcome_kind; /* 1=promoted 2=held 3=refused */
    int32_t check_type, check_arity, check_bounds, check_table;
    int32_t bypass_kind;  /* 0 none, 1 type, 2 arity, 3 bounds, 4 table */
    int32_t benign_kind;  /* 0 none, 1 type_stable, 2 table_stable, 3 epoch_bumped */
    int32_t host_call_permitted;
};

struct case_out {
    char id[MAX_ID];
    char outcome[MAX_KIND];
    int32_t host_call_permitted;
    char category[MAX_CATEGORY];
    int32_t check_type, check_arity, check_bounds, check_table;
};

#endif
