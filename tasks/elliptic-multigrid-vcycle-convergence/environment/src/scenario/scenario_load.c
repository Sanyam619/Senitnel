#include "scenario.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Parse a scenario descriptor file. Format is a simple key = value
 * table; lines starting with '#' or blank lines are ignored. */
int scenario_load(const char *path, scenario_t *out) {
    if (!path || !out) {
        return -1;
    }
    FILE *fp = fopen(path, "r");
    if (!fp) {
        return -1;
    }
    memset(out, 0, sizeof(*out));
    /* Default the label to the file stem. */
    const char *slash = strrchr(path, '/');
    const char *base = slash ? slash + 1 : path;
    const char *dot = strrchr(base, '.');
    size_t len = dot ? (size_t)(dot - base) : strlen(base);
    if (len >= sizeof(out->label)) {
        len = sizeof(out->label) - 1;
    }
    memcpy(out->label, base, len);
    out->label[len] = '\0';
    out->budget = -1;

    char line[256];
    while (fgets(line, sizeof(line), fp)) {
        char *p = line;
        while (*p == ' ' || *p == '\t') p++;
        if (*p == '#' || *p == '\n' || *p == '\0') continue;
        char key[64], val[LAW_STR_MAX];
        if (sscanf(p, " %63[^= \t] = %95[^\n]", key, val) != 2) {
            continue;
        }
        /* Trim trailing whitespace from val. */
        size_t vlen = strlen(val);
        while (vlen > 0 && (val[vlen - 1] == ' ' || val[vlen - 1] == '\t' ||
                            val[vlen - 1] == '\r')) {
            val[--vlen] = '\0';
        }
        if (strcmp(key, "nx") == 0) {
            out->nx = atoi(val);
        } else if (strcmp(key, "ny") == 0) {
            out->ny = atoi(val);
        } else if (strcmp(key, "kx_law") == 0) {
            snprintf(out->kx_law, sizeof(out->kx_law), "%s", val);
        } else if (strcmp(key, "ky_law") == 0) {
            snprintf(out->ky_law, sizeof(out->ky_law), "%s", val);
        } else if (strcmp(key, "rhs_law") == 0) {
            snprintf(out->rhs_law, sizeof(out->rhs_law), "%s", val);
        } else if (strcmp(key, "budget") == 0) {
            out->budget = atoi(val);
        } else if (strcmp(key, "label") == 0) {
            snprintf(out->label, sizeof(out->label), "%s", val);
        }
    }
    fclose(fp);
    if (out->nx <= 0 || out->ny <= 0 || out->budget <= 0) {
        return -1;
    }
    if (out->kx_law[0] == '\0' || out->ky_law[0] == '\0' ||
        out->rhs_law[0] == '\0') {
        return -1;
    }
    return 0;
}
