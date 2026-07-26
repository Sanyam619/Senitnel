#!/usr/bin/env bash
set -euo pipefail

cd /opt/kernlab

cat > kern/a7/weave.c <<'CEOF'
#include "klb_types.h"
#include <stdio.h>
#include <string.h>

int op_weave(const char *path, KlbWeave *out) {
    FILE *f = fopen(path, "r");
    if (!f) return -1;
    memset(out, 0, sizeof *out);
    char line[512];
    while (fgets(line, sizeof line, f)) {
        if (line[0] == '#') continue;
        char tag[16];
        if (sscanf(line, "%15s", tag) != 1) continue;
        if (strcmp(tag, "LCK") == 0 && out->n_gate < KLB_MAX_STEPS) {
            KlbGateEvt *e = &out->gate[out->n_gate++];
            sscanf(line, "%*s %lld %31s %31s", (long long *)&e->ts, e->actor, e->gate);
            char op[16];
            sscanf(line, "%*s %*s %*s %*s %15s", op);
            e->is_wait = (strcmp(op, "WAIT") == 0);
            e->is_rel = (strcmp(op, "REL") == 0);
        } else if (strcmp(tag, "TSW") == 0 && out->n_switch < KLB_MAX_STEPS) {
            KlbSwitchEvt *s = &out->sw[out->n_switch++];
            sscanf(line, "%*s %lld %31s %31s", (long long *)&s->ts, s->prev, s->next);
        } else if (strcmp(tag, "TMR") == 0) {
            char op[16];
            char who[32];
            int64_t ts, dl;
            sscanf(line, "%*s %lld %31s %*s %15s %lld", (long long *)&ts, who, op, (long long *)&dl);
            if (strcmp(op, "EXP") == 0) {
                strncpy(out->missed, who, 31);
                out->miss_ts = ts;
            }
        }
    }
    fclose(f);
    return 0;
}
CEOF

cat > relay/m3/latch.c <<'CEOF'
#include "klb_types.h"
#include <string.h>

static int gate_index(const char *gate, char gates[][32], int *n) {
    for (int i = 0; i < *n; i++) if (strcmp(gates[i], gate) == 0) return i;
    if (*n < KLB_MAX_GATES) {
        strncpy(gates[*n], gate, 31);
        return (*n)++;
    }
    return 0;
}

int op_latch(const KlbWeave *w, KlbLatch *out) {
    memset(out, 0, sizeof *out);
    char gates[KLB_MAX_GATES][32];
    char holders[KLB_MAX_GATES][32];
    int n_gates = 0;
    char running[32] = "";
    char wait_gate[32] = "";
    int order[KLB_MAX_STEPS];
    int n_order = 0;
    for (int i = 0; i < w->n_gate; i++) {
        if (w->gate[i].ts <= w->miss_ts) order[n_order++] = i;
    }
    for (int a = 1; a < n_order; a++) {
        int key = order[a];
        int64_t ts = w->gate[key].ts;
        int b = a - 1;
        while (b >= 0 && w->gate[order[b]].ts > ts) {
            order[b + 1] = order[b];
            b--;
        }
        order[b + 1] = key;
    }
    for (int oi = 0; oi < n_order; oi++) {
        const KlbGateEvt *e = &w->gate[order[oi]];
        int gi = gate_index(e->gate, gates, &n_gates);
        if (e->is_wait) {
            if (strcmp(e->actor, w->missed) == 0) strncpy(wait_gate, e->gate, 31);
            continue;
        }
        if (e->is_rel) {
            holders[gi][0] = '\0';
            continue;
        }
        strncpy(holders[gi], e->actor, 31);
    }
    for (int si = 0; si < w->n_switch; si++) {
        if (w->sw[si].ts <= w->miss_ts) strncpy(running, w->sw[si].next, 31);
    }
    if (wait_gate[0]) {
        int gi = gate_index(wait_gate, gates, &n_gates);
        strncpy(out->holder[0], holders[gi], 31);
    }
    strncpy(out->running, running, 31);
    out->at_ts = w->miss_ts;
    return 0;
}
CEOF

cat > span/q9/span.c <<'CEOF'
#include "klb_types.h"
#include <string.h>

int op_span(const KlbLatch *l, const char *tgt, char chain[3][32]) {
    strncpy(chain[0], tgt, 31);
    strncpy(chain[1], l->holder[0], 31);
    strncpy(chain[2], l->running, 31);
    return 0;
}
CEOF

cat > lift/w2/lift.c <<'CEOF'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int op_lift(const char *cfg, const char *tgt, int *ceilings, int cap) {
    int wait_band = 0;
    FILE *f = fopen(cfg, "r");
    if (!f) return -1;
    char line[256];
    char section[64] = "";
    int n_gate = 0;
    while (fgets(line, sizeof line, f)) {
        if (line[0] == '[') {
            char *end = strchr(line, ']');
            if (!end) continue;
            *end = '\0';
            strncpy(section, line + 1, sizeof section - 1);
            continue;
        }
        char key[64], val[64];
        if (sscanf(line, " %63[^= ] = %63s", key, val) != 2) continue;
        if (strcmp(section, "actors") == 0) {
            char *dot = strchr(key, '.');
            if (!dot) continue;
            *dot = '\0';
            if (strcmp(key, tgt) == 0 && strcmp(dot + 1, "band") == 0) wait_band = atoi(val);
        } else if (strcmp(section, "gates") == 0) {
            char key[64], val[64];
            if (sscanf(line, " %63[^= ] = %63s", key, val) != 2) continue;
            char *dot = strchr(key, '.');
            if (dot && strcmp(dot + 1, "present") == 0) n_gate++;
        }
    }
    fclose(f);
    for (int i = 0; i < n_gate && i < cap; i++) ceilings[i] = wait_band;
    return n_gate;
}
CEOF

cat > src/probe/stage_a.c <<'CEOF'
#include "klb_types.h"
#include <string.h>

int op_weave(const char *path, KlbWeave *out);
int op_latch(const KlbWeave *w, KlbLatch *out);

int stage_a(const char *trace, KlbWeave *w, KlbLatch *l, char missed[32]) {
    if (op_weave(trace, w) != 0) return -1;
    if (op_latch(w, l) != 0) return -1;
    strncpy(missed, w->missed, 31);
    return 0;
}
CEOF

make clean
make all
mkdir -p bin
mv -f kernprobe bin/

mkdir -p /output
/opt/kernlab/bin/kernprobe --manifest /opt/kernlab/config/manifest.txt --out /output/analysis.json
