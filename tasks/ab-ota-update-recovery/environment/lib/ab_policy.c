#include "ab_policy.h"

#include <ctype.h>
#include <stdio.h>
#include <string.h>

static void trim(char *s) {
    char *end;
    while (*s && isspace((unsigned char)*s)) s++;
    if (!*s) return;
    end = s + strlen(s) - 1;
    while (end > s && isspace((unsigned char)*end)) *end-- = '\0';
}

const char *ab_rule_name(ab_rule_id_t id) {
    switch (id) {
    case AB_RULE_ROLLBACK_STAGING_B:
        return "rollback_staging_b";
    case AB_RULE_REPOINT_LIVE_B_FAIL:
        return "repoint_live_b_fail";
    case AB_RULE_COMMIT_STAGING_A:
        return "commit_staging_a";
    case AB_RULE_ROLLBACK_LIVE_B_FAIL:
        return "rollback_live_b_fail";
    case AB_RULE_HOLD:
        return "hold";
    default:
        return NULL;
    }
}

int ab_rule_from_name(const char *name, ab_rule_id_t *out) {
    if (!name || !out) return -1;
    for (int i = 0; i < AB_RULE_COUNT; i++) {
        const char *n = ab_rule_name((ab_rule_id_t)i);
        if (n && strcmp(n, name) == 0) {
            *out = (ab_rule_id_t)i;
            return 0;
        }
    }
    return -1;
}

int ab_policy_default(ab_recovery_policy_t *out) {
    if (!out) return -1;
    out->rule_order[0] = AB_RULE_ROLLBACK_STAGING_B;
    out->rule_order[1] = AB_RULE_REPOINT_LIVE_B_FAIL;
    out->rule_order[2] = AB_RULE_COMMIT_STAGING_A;
    out->rule_order[3] = AB_RULE_ROLLBACK_LIVE_B_FAIL;
    out->rule_order[4] = AB_RULE_HOLD;
    out->rule_count = AB_RULE_COUNT;
    out->allow_commit = 1;
    return 0;
}

static int parse_rule_order(const char *value, ab_recovery_policy_t *out) {
    char buf[512];
    if (strlen(value) >= sizeof(buf)) return -1;
    strcpy(buf, value);
    out->rule_count = 0;
    for (char *tok = strtok(buf, ","); tok; tok = strtok(NULL, ",")) {
        trim(tok);
        ab_rule_id_t id;
        if (ab_rule_from_name(tok, &id)) return -1;
        if (out->rule_count >= AB_RULE_COUNT) return -1;
        out->rule_order[out->rule_count++] = id;
    }
    return out->rule_count > 0 ? 0 : -1;
}

static int parse_bool(const char *value) {
    if (!value) return 0;
    if (strcmp(value, "true") == 0 || strcmp(value, "1") == 0 || strcmp(value, "yes") == 0) return 1;
    return 0;
}

int ab_policy_load(const char *path, ab_recovery_policy_t *out) {
    if (!path || !out) return -1;
    if (ab_policy_default(out)) return -1;
    FILE *fp = fopen(path, "r");
    if (!fp) return -1;
    char line[512];
    while (fgets(line, sizeof(line), fp)) {
        char *hash = strchr(line, '#');
        if (hash) *hash = '\0';
        trim(line);
        if (!*line) continue;
        char *eq = strchr(line, '=');
        if (!eq) continue;
        *eq++ = '\0';
        trim(line);
        trim(eq);
        if (strcmp(line, "rule_order") == 0) {
            if (parse_rule_order(eq, out)) {
                fclose(fp);
                return -1;
            }
        } else if (strcmp(line, "allow_commit") == 0) {
            out->allow_commit = parse_bool(eq);
        }
    }
    fclose(fp);
    return 0;
}
