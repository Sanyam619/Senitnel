#ifndef TIER_POLICY_H
#define TIER_POLICY_H

#include "../include/lab.h"

#define MAX_ROSTER 16
#define MAX_HOLDS 16
#define MAX_GEN 32

typedef struct {
    char name[64];
    char klass[32];
    int epoch;
} RosterRow;

typedef struct {
    int floor;
    char lane_ns[32];
    char lane_kind[32];
    char anchor_ns[32];
    char anchor_kind[32];
} CutoverWindow;

int read_policy_gen(char *out, int n);
int load_roster(RosterRow *rows, int cap);
int load_cutover(CutoverWindow *win);
int load_holds(char names[][64], int cap);
int path_on_hold(const char *name, char holds[][64], int hcount);
int row_migrates(const RosterRow *row, const CutoverWindow *win,
                 char holds[][64], int hcount);
int roster_migrate_names(char out[][64], int cap);

#endif
