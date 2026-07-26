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
            e->is_wait = 0;
            e->is_rel = 0;
        } else if (strcmp(tag, "TMR") == 0) {
            char op[16];
            sscanf(line, "%*s %lld %31s %*s %15s %lld", (long long *)&out->miss_ts, out->missed, op, (long long *)&out->miss_ts);
        }
    }
    fclose(f);
    return 0;
}
