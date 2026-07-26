#include "tier_policy.h"
#include "state_io.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int read_policy_gen(char *out, int n) {
    if (!out || n <= 0) return -1;
    if (read_text(POLICY_GEN, out, n) != 0) {
        snprintf(out, (size_t)n, "g2");
        return 0;
    }
    return 0;
}

static void gen_path(char *out, int n, const char *file) {
    char gen[MAX_GEN];
    read_policy_gen(gen, sizeof(gen));
    snprintf(out, (size_t)n, "%s/%s/%s", GEN_ROOT, gen, file);
}

int load_roster(RosterRow *rows, int cap) {
    if (!rows || cap <= 0) return -1;
    char path[512];
    gen_path(path, sizeof(path), "roster.conf");
    FILE *f = fopen(path, "r");
    if (!f) return -1;
    int n = 0;
    char line[256];
    while (fgets(line, sizeof(line), f) && n < cap) {
        if (line[0] == '#' || line[0] == '\n' || line[0] == '\r') continue;
        char name[64], klass[32];
        int epoch = 0;
        if (sscanf(line, "%63s %31s %d", name, klass, &epoch) != 3) continue;
        snprintf(rows[n].name, sizeof(rows[n].name), "%s", name);
        snprintf(rows[n].klass, sizeof(rows[n].klass), "%s", klass);
        rows[n].epoch = epoch;
        n++;
    }
    fclose(f);
    return n;
}

int load_cutover(CutoverWindow *win) {
    if (!win) return -1;
    memset(win, 0, sizeof(*win));
    win->floor = 0;
    snprintf(win->lane_ns, sizeof(win->lane_ns), "broker");
    snprintf(win->lane_kind, sizeof(win->lane_kind), "filesystem");
    snprintf(win->anchor_ns, sizeof(win->anchor_ns), "host");
    snprintf(win->anchor_kind, sizeof(win->anchor_kind), "inode");

    char path[512];
    gen_path(path, sizeof(path), "cutover.toml");
    FILE *f = fopen(path, "r");
    if (!f) return -1;
    char line[256];
    char section[64] = "";
    while (fgets(line, sizeof(line), f)) {
        char *p = line;
        while (*p == ' ' || *p == '\t') p++;
        if (*p == '#' || *p == '\n' || *p == '\r') continue;
        if (*p == '[') {
            sscanf(p, "[%63[^]]]", section);
            continue;
        }
        char key[64], val[64];
        if (sscanf(p, "%63[^=]=%63s", key, val) != 2) continue;
        for (char *k = key + strlen(key); k > key && (k[-1] == ' ' || k[-1] == '\t'); ) *--k = 0;
        char *ks = key;
        while (*ks == ' ' || *ks == '\t') ks++;
        if (ks != key) memmove(key, ks, strlen(ks) + 1);
        if (val[0] == '"') {
            size_t L = strlen(val);
            if (L >= 2 && val[L - 1] == '"') {
                val[L - 1] = 0;
                memmove(val, val + 1, L - 1);
            }
        }
        if (strcmp(section, "window") == 0 && strcmp(key, "floor") == 0) {
            win->floor = atoi(val);
        } else if (strcmp(section, "lane") == 0) {
            if (strcmp(key, "ns") == 0) snprintf(win->lane_ns, sizeof(win->lane_ns), "%s", val);
            else if (strcmp(key, "kind") == 0) snprintf(win->lane_kind, sizeof(win->lane_kind), "%s", val);
        } else if (strcmp(section, "anchor") == 0) {
            if (strcmp(key, "ns") == 0) snprintf(win->anchor_ns, sizeof(win->anchor_ns), "%s", val);
            else if (strcmp(key, "kind") == 0) snprintf(win->anchor_kind, sizeof(win->anchor_kind), "%s", val);
        }
    }
    fclose(f);
    return 0;
}

int load_holds(char names[][64], int cap) {
    if (!names || cap <= 0) return -1;
    char path[512];
    gen_path(path, sizeof(path), "holds.conf");
    FILE *f = fopen(path, "r");
    if (!f) return 0;
    int n = 0;
    char line[256];
    while (fgets(line, sizeof(line), f) && n < cap) {
        if (line[0] == '#' || line[0] == '\n' || line[0] == '\r') continue;
        char name[64];
        if (sscanf(line, "%63s", name) != 1) continue;
        snprintf(names[n], 64, "%s", name);
        n++;
    }
    fclose(f);
    return n;
}

int path_on_hold(const char *name, char holds[][64], int hcount) {
    if (!name) return 0;
    for (int i = 0; i < hcount; i++) {
        if (strcmp(holds[i], name) == 0) return 1;
    }
    return 0;
}

int row_migrates(const RosterRow *row, const CutoverWindow *win,
                 char holds[][64], int hcount) {
    if (!row || !win) return 0;
    if (path_on_hold(row->name, holds, hcount)) return 0;
    if (strcmp(row->klass, "anchor") == 0) return 0;
    if (strcmp(row->klass, "lane") != 0) return 0;
    return row->epoch >= win->floor;
}

int roster_migrate_names(char out[][64], int cap) {
    RosterRow rows[MAX_ROSTER];
    CutoverWindow win;
    char holds[MAX_HOLDS][64];
    int n = load_roster(rows, MAX_ROSTER);
    if (n < 0) return -1;
    if (load_cutover(&win) != 0) return -1;
    int hcount = load_holds(holds, MAX_HOLDS);
    if (hcount < 0) hcount = 0;
    int o = 0;
    for (int i = 0; i < n && o < cap; i++) {
        if (row_migrates(&rows[i], &win, holds, hcount)) {
            snprintf(out[o], 64, "%s", rows[i].name);
            o++;
        }
    }
    return o;
}
