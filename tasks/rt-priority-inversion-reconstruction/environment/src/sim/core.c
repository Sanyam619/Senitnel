#include "klb_fmt.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int read_prio_toml(const char *path, const char *actor, int *prio) {
    FILE *f = fopen(path, "r");
    if (!f) return -1;
    char line[256];
    char section[64] = "";
    while (fgets(line, sizeof line, f)) {
        if (line[0] == '[') {
            char *end = strchr(line, ']');
            if (!end) continue;
            *end = '\0';
            strncpy(section, line + 1, sizeof section - 1);
            continue;
        }
        if (strcmp(section, "actors") != 0) continue;
        char key[64], val[64];
        if (sscanf(line, " %63[^= ] = %63s", key, val) != 2) continue;
        char *dot = strchr(key, '.');
        if (!dot) continue;
        *dot = '\0';
        if (strcmp(key, actor) == 0 && strcmp(dot + 1, "band") == 0) {
            *prio = atoi(val);
            fclose(f);
            return 0;
        }
    }
    fclose(f);
    return -1;
}

int klb_load_set(const char *path, char actors[][32], int prios[], char gates[][32], int *n_act, int *n_gate) {
    FILE *f = fopen(path, "r");
    if (!f) return -1;
    *n_act = 0;
    *n_gate = 0;
    char line[256];
    char section[64] = "";
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
            int idx = -1;
            for (int i = 0; i < *n_act; i++) if (strcmp(actors[i], key) == 0) idx = i;
            if (idx < 0) {
                idx = (*n_act)++;
                strncpy(actors[idx], key, 31);
            }
            if (strcmp(dot + 1, "band") == 0) prios[idx] = atoi(val);
        } else if (strcmp(section, "gates") == 0) {
            char key[64], val[64];
            if (sscanf(line, " %63[^= ] = %63s", key, val) != 2) continue;
            char *dot = strchr(key, '.');
            if (!dot) continue;
            *dot = '\0';
            if (strcmp(dot + 1, "present") == 0) {
                strncpy(gates[(*n_gate)++], key, 31);
            }
        }
    }
    fclose(f);
    (void)read_prio_toml;
    return 0;
}

int klb_parse_trace(const char *path, KlbWeave *out) {
    FILE *f = fopen(path, "r");
    if (!f) return -1;
    memset(out, 0, sizeof *out);
    char line[512];
    while (fgets(line, sizeof line, f)) {
        if (line[0] == '#') continue;
        char tag[16];
        if (sscanf(line, "%15s", tag) != 1) continue;
        if (strcmp(tag, "LCK") == 0) {
            KlbGateEvt *e = &out->gate[out->n_gate++];
            sscanf(line, "%*s %lld %31s %31s", (long long *)&e->ts, e->actor, e->gate);
            char op[16];
            sscanf(line, "%*s %*s %*s %*s %15s", op);
            e->is_wait = (strcmp(op, "WAIT") == 0);
            e->is_rel = (strcmp(op, "REL") == 0);
        } else if (strcmp(tag, "TSW") == 0) {
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
