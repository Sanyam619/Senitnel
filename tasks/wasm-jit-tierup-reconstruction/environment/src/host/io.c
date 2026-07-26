#include "host.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void trim(char *s) {
    size_t n;
    char *p = s;
    while (*p == ' ' || *p == '\t') p++;
    if (p != s) memmove(s, p, strlen(p) + 1);
    n = strlen(s);
    while (n > 0 && (s[n - 1] == '\n' || s[n - 1] == '\r' || s[n - 1] == ' ')) {
        s[--n] = '\0';
    }
}

static int kv_file(const char *path, int (*on)(const char *, const char *, void *), void *ud) {
    FILE *fp = fopen(path, "r");
    char line[MAX_LINE];
    if (!fp) return -1;
    while (fgets(line, sizeof(line), fp)) {
        char *eq;
        trim(line);
        if (!line[0] || line[0] == '#') continue;
        eq = strchr(line, '=');
        if (!eq) continue;
        *eq = '\0';
        trim(line);
        trim(eq + 1);
        if (on(line, eq + 1, ud) != 0) {
            fclose(fp);
            return -1;
        }
    }
    fclose(fp);
    return 0;
}

static int on_sc(const char *k, const char *v, void *ud) {
    struct scenario_in *o = ud;
    if (!strcmp(k, "id")) snprintf(o->id, sizeof(o->id), "%s", v);
    else if (!strcmp(k, "is_hot")) o->is_hot = (int)strtol(v, NULL, 10);
    else if (!strcmp(k, "is_very_hot")) o->is_very_hot = (int)strtol(v, NULL, 10);
    else if (!strcmp(k, "triggers_reload")) o->triggers_reload = (int)strtol(v, NULL, 10);
    else if (!strcmp(k, "attempts_host_call")) o->attempts_host_call = (int)strtol(v, NULL, 10);
    else if (!strcmp(k, "host_is_legit")) o->host_is_legit = (int)strtol(v, NULL, 10);
    else if (!strcmp(k, "live_table")) o->live_table = (int)strtol(v, NULL, 10);
    return 0;
}

static int on_prof(const char *k, const char *v, void *ud) {
    struct profile_view *o = ud;
    if (!strcmp(k, "id")) snprintf(o->id, sizeof(o->id), "%s", v);
    else if (!strcmp(k, "has_profile")) o->has_profile = (int)strtol(v, NULL, 10);
    else if (!strcmp(k, "polymorphic")) o->polymorphic = (int)strtol(v, NULL, 10);
    else if (!strcmp(k, "probe_count")) o->probe_count = (int)strtol(v, NULL, 10);
    else if (!strcmp(k, "reload_seen")) o->reload_seen = (int)strtol(v, NULL, 10);
    else if (!strcmp(k, "epoch_stamp")) o->epoch_stamp_raw = (uint32_t)strtoul(v, NULL, 10);
    else if (!strcmp(k, "trust_mark")) o->trust_mark = (int)strtol(v, NULL, 10);
    return 0;
}

static int on_rb(const char *k, const char *v, void *ud) {
    struct rebind_view *o = ud;
    if (!strcmp(k, "id")) snprintf(o->id, sizeof(o->id), "%s", v);
    else if (!strcmp(k, "recorded")) o->recorded = (int)strtol(v, NULL, 10);
    else if (!strcmp(k, "old_type")) snprintf(o->old_type, sizeof(o->old_type), "%s", v);
    else if (!strcmp(k, "new_type")) snprintf(o->new_type, sizeof(o->new_type), "%s", v);
    else if (!strcmp(k, "old_arity")) o->old_arity = (int)strtol(v, NULL, 10);
    else if (!strcmp(k, "new_arity")) o->new_arity = (int)strtol(v, NULL, 10);
    else if (!strcmp(k, "old_bounds")) o->old_bounds = (int)strtol(v, NULL, 10);
    else if (!strcmp(k, "new_bounds")) o->new_bounds = (int)strtol(v, NULL, 10);
    else if (!strcmp(k, "old_table")) o->old_table = (int)strtol(v, NULL, 10);
    else if (!strcmp(k, "new_table")) o->new_table = (int)strtol(v, NULL, 10);
    return 0;
}

static int on_fl(const char *k, const char *v, void *ud) {
    struct floor_view *o = ud;
    if (!strcmp(k, "id")) snprintf(o->id, sizeof(o->id), "%s", v);
    else if (!strcmp(k, "hint_outcome")) snprintf(o->hint_outcome, sizeof(o->hint_outcome), "%s", v);
    else if (!strcmp(k, "hint_category")) snprintf(o->hint_category, sizeof(o->hint_category), "%s", v);
    else if (!strcmp(k, "hint_host")) o->hint_host = (int)strtol(v, NULL, 10);
    return 0;
}

int load_scenario(const char *path, struct scenario_in *out) {
    memset(out, 0, sizeof(*out));
    return kv_file(path, on_sc, out) == 0 && out->id[0] ? 0 : -1;
}

int load_profile(const char *path, struct profile_view *out) {
    memset(out, 0, sizeof(*out));
    return kv_file(path, on_prof, out) == 0 && out->id[0] ? 0 : -1;
}

int load_rebind(const char *path, struct rebind_view *out) {
    memset(out, 0, sizeof(*out));
    return kv_file(path, on_rb, out) == 0 && out->id[0] ? 0 : -1;
}

int load_floor(const char *path, struct floor_view *out) {
    memset(out, 0, sizeof(*out));
    return kv_file(path, on_fl, out) == 0 && out->id[0] ? 0 : -1;
}

int read_registry_epoch(const char *path, uint32_t *epoch) {
    FILE *fp = fopen(path, "r");
    char line[MAX_LINE];
    if (!fp || !epoch) {
        if (fp) fclose(fp);
        return -1;
    }
    *epoch = 0;
    while (fgets(line, sizeof(line), fp)) {
        trim(line);
        if (!strncmp(line, "epoch=", 6)) {
            *epoch = (uint32_t)strtoul(line + 6, NULL, 10);
            fclose(fp);
            return 0;
        }
    }
    fclose(fp);
    return -1;
}
