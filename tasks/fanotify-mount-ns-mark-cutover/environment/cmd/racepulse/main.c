#include "../../include/lab.h"
#include "../../lib/state_io.h"
#include "../../lib/tier_policy.h"
#include <dirent.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

static int file_has_private_yes(const char *path) {
    char buf[8192];
    if (read_text(path, buf, sizeof(buf)) != 0) return 0;
    return strstr(buf, "PrivateMounts=yes") != NULL;
}

static int walk_private_yes(const char *dir) {
    DIR *d = opendir(dir);
    if (!d) return 0;
    struct dirent *ent;
    int found = 0;
    while ((ent = readdir(d)) != NULL) {
        if (ent->d_name[0] == '.') continue;
        char p[512];
        snprintf(p, sizeof(p), "%s/%s", dir, ent->d_name);
        struct stat st;
        if (stat(p, &st) != 0) continue;
        if (S_ISDIR(st.st_mode)) {
            if (walk_private_yes(p)) { found = 1; break; }
        } else if (S_ISREG(st.st_mode)) {
            if (file_has_private_yes(p)) { found = 1; break; }
        }
    }
    closedir(d);
    return found;
}

static int check_state(void) {
    RosterRow rows[MAX_ROSTER];
    CutoverWindow win;
    char holds[MAX_HOLDS][64];
    int n = load_roster(rows, MAX_ROSTER);
    if (n < 0) return 0;
    if (load_cutover(&win) != 0) return 0;
    int hcount = load_holds(holds, MAX_HOLDS);
    if (hcount < 0) hcount = 0;

    char mnt[64];
    if (read_text(MNT_ID, mnt, sizeof(mnt)) != 0) return 0;
    if (strcmp(mnt, "broker") != 0) return 0;

    char ok[32];
    if (read_text(INHERIT_OK, ok, sizeof(ok)) != 0 || strcmp(ok, "1") != 0) return 0;

    if (walk_private_yes("/data/lab/units")) return 0;

    char table[4096];
    if (read_text(INHERIT_TABLE, table, sizeof(table)) != 0) return 0;

    char migrate[MAX_ROSTER][64];
    int mcount = 0;
    for (int i = 0; i < n; i++) {
        const char *name = rows[i].name;
        char bt[512], ht[512], bm[512], hm[512];
        snprintf(bt, sizeof(bt), "%s/%s", BROKER_TREE, name);
        snprintf(ht, sizeof(ht), "%s/%s", HOST_TREE, name);
        snprintf(bm, sizeof(bm), "%s/%s", BROKER_MARKS, name);
        snprintf(hm, sizeof(hm), "%s/%s", HOST_MARKS, name);

        if (row_migrates(&rows[i], &win, holds, hcount)) {
            if (!file_exists(bt) || file_exists(ht)) return 0;
            if (!file_exists(bm) || file_exists(hm)) return 0;
            char kind[64];
            if (read_text(bm, kind, sizeof(kind)) != 0) return 0;
            if (strcmp(kind, win.lane_kind) != 0) return 0;
            if (mcount < MAX_ROSTER) {
                snprintf(migrate[mcount], 64, "%s", name);
                mcount++;
            }
        } else {
            if (file_exists(bt) || !file_exists(ht)) return 0;
            if (file_exists(bm) || !file_exists(hm)) return 0;
            char kind[64];
            if (read_text(hm, kind, sizeof(kind)) != 0) return 0;
            if (strcmp(kind, win.anchor_kind) != 0) return 0;
        }
    }

    char *save = NULL;
    char tbuf[4096];
    snprintf(tbuf, sizeof(tbuf), "%s", table);
    int seen = 0;
    for (char *line = strtok_r(tbuf, "\n", &save); line; line = strtok_r(NULL, "\n", &save)) {
        if (!line[0]) continue;
        char expect[128];
        if (seen >= mcount) return 0;
        snprintf(expect, sizeof(expect), "%s:remount-ok", migrate[seen]);
        if (strcmp(line, expect) != 0) return 0;
        seen++;
    }
    if (seen != mcount) return 0;
    return 1;
}

static void clear_jitter(void) {
    DIR *d = opendir(HOST_JITTER);
    if (!d) return;
    struct dirent *ent;
    while ((ent = readdir(d)) != NULL) {
        if (ent->d_name[0] == '.') continue;
        char p[512];
        snprintf(p, sizeof(p), "%s/%s", HOST_JITTER, ent->d_name);
        unlink(p);
    }
    closedir(d);
}

int main(void) {
    ensure_dir(HOST_JITTER);
    if (check_state()) {
        clear_jitter();
        write_text(RACE_FLAG, "clean");
        printf("clean\n");
        return 0;
    }
    for (int i = 0; i < NUM_PATHS; i++) {
        char jp[512];
        snprintf(jp, sizeof(jp), "%s/%s", HOST_JITTER, ALL_PATHS[i]);
        write_text(jp, "jitter");
    }
    write_text(RACE_FLAG, "dirty");
    printf("dirty\n");
    return 1;
}
