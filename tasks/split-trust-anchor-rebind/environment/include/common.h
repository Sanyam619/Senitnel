#ifndef COMMON_H
#define COMMON_H

#include <stdint.h>
#include <stddef.h>

#define MAX_LINE 256
#define MAX_ID 64
#define MAX_LIN 64
#define MAX_CASES 32

struct row_a {
    uint32_t store_gen;
    uint32_t runtime_epoch;
    uint32_t restore_gen;
};

struct slot_a {
    int ok;
    uint32_t bound_gen;
};

struct row_b {
    char subject_lin[MAX_LIN];
    char claim_lin[MAX_LIN];
    char active_lin[MAX_LIN];
    char restore_lin[MAX_LIN];
};

struct slot_b {
    int ok;
    int used_restore;
};

struct row_c {
    char tok_id[MAX_ID];
    int cached_ok;
    int refresh;
    int in_current;
    int in_cached;
};

struct slot_c {
    int ok;
    int stale;
};

struct case_in {
    char id[MAX_ID];
    uint32_t store_gen;
    char subject_lin[MAX_LIN];
    char claim_lin[MAX_LIN];
    char tok_id[MAX_ID];
    int cached_ok;
    int refresh;
};

struct case_out {
    char id[MAX_ID];
    char decision[16];
    char reason_code[32];
};

#endif
