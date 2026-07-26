#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int op_lift(const char *cfg, const char *tgt, int *ceilings, int cap) {
    (void)tgt;
    FILE *f = fopen(cfg, "r");
    if (!f) return -1;
    char line[256];
    char section[64] = "";
    int idx = 0;
    int min_band = 9999;
    while (fgets(line, sizeof line, f) && idx < cap) {
        if (line[0] == '[') {
            char *end = strchr(line, ']');
            if (!end) continue;
            *end = '\0';
            strncpy(section, line + 1, sizeof section - 1);
            continue;
        }
        if (strcmp(section, "actors") == 0) {
            char key[64], val[64];
            if (sscanf(line, " %63[^= ] = %63s", key, val) == 2) {
                char *dot = strchr(key, '.');
                if (dot && strcmp(dot + 1, "band") == 0) {
                    int band = atoi(val);
                    if (band < min_band) min_band = band;
                    ceilings[idx++] = band;
                }
            }
        }
    }
    fclose(f);
    int n_gate = 0;
    f = fopen(cfg, "r");
    section[0] = '\0';
    while (f && fgets(line, sizeof line, f)) {
        if (line[0] == '[') {
            char *end = strchr(line, ']');
            if (!end) continue;
            *end = '\0';
            strncpy(section, line + 1, sizeof section - 1);
        } else if (strcmp(section, "gates") == 0) {
            char key[64], val[64];
            if (sscanf(line, " %63[^= ] = %63s", key, val) == 2) {
                char *dot = strchr(key, '.');
                if (dot && strcmp(dot + 1, "present") == 0) n_gate++;
            }
        }
    }
    if (f) fclose(f);
    for (int i = 0; i < n_gate && i < cap; i++) ceilings[i] = min_band;
    return n_gate;
}
